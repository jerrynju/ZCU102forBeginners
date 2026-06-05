// SPDX-License-Identifier: GPL-2.0
/*
 * Traffic Edge 视频采集驱动
 * 管理 AXI VDMA 的帧缓冲区，通过 V4L2 接口暴露给用户空间
 *
 * 每个通道对应一个 /dev/videoN 设备节点
 * 使用 DMABUF 内存类型，实现零拷贝传输
 */

#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_address.h>
#include <linux/dmaengine.h>
#include <linux/dma-mapping.h>
#include <linux/interrupt.h>
#include <linux/clk.h>
#include <media/v4l2-device.h>
#include <media/v4l2-ioctl.h>
#include <media/v4l2-event.h>
#include <media/videobuf2-dma-contig.h>
#include <media/videobuf2-v4l2.h>

#define DRIVER_NAME     "traffic-video"
#define NUM_CHANNELS    4
#define NUM_BUFS        3         /* 三重缓冲 */
#define FRAME_WIDTH     1920
#define FRAME_HEIGHT    1080
#define FRAME_FORMAT    V4L2_PIX_FMT_NV12

/* VDMA 寄存器偏移（Xilinx AXI VDMA，S2MM 方向）*/
#define VDMA_S2MM_CR        0x30   /* 控制寄存器 */
#define VDMA_S2MM_SR        0x34   /* 状态寄存器 */
#define VDMA_S2MM_FRMCNT    0x38   /* 帧计数 */
#define VDMA_S2MM_VSIZE     0xA0   /* 垂直尺寸（触发传输）*/
#define VDMA_S2MM_HSIZE     0xA4   /* 水平尺寸（字节）*/
#define VDMA_S2MM_FRMSTORE  0xA8   /* 帧存储数量 */
#define VDMA_S2MM_BUFTHRES  0xAC   /* 行缓冲阈值 */
#define VDMA_S2MM_ADDR_BASE 0xAC   /* 起始地址寄存器组 */

#define VDMA_CR_RUN         BIT(0)
#define VDMA_CR_FRMCNT_EN   BIT(4)
#define VDMA_CR_IRQEN_ERR   BIT(14)
#define VDMA_CR_IRQEN_DLY   BIT(13)
#define VDMA_CR_IRQEN_FRM   BIT(12)

struct traffic_buf {
    struct vb2_v4l2_buffer vb;
    struct list_head       list;
    dma_addr_t             dma_addr;
};

struct traffic_video_ch {
    struct v4l2_device    v4l2_dev;
    struct video_device   vdev;
    struct vb2_queue      queue;
    struct mutex          lock;
    spinlock_t            irq_lock;
    struct list_head      buf_list;   /* 就绪缓冲区队列 */

    void __iomem         *vdma_base; /* VDMA 寄存器映射 */
    int                   irq;
    int                   channel;

    /* 当前活跃帧缓冲区 */
    struct traffic_buf   *active_buf;

    /* 帧计数器 */
    u32                   frame_count;
    bool                  streaming;
};

static struct traffic_video_ch *g_channels[NUM_CHANNELS];

/* ── VDMA 操作 ─────────────────────────────────────────────── */
static void vdma_write(struct traffic_video_ch *ch, u32 offset, u32 val) {
    iowrite32(val, ch->vdma_base + offset);
}

static u32 vdma_read(struct traffic_video_ch *ch, u32 offset) {
    return ioread32(ch->vdma_base + offset);
}

static void vdma_set_frame_addr(struct traffic_video_ch *ch,
                                int slot, dma_addr_t addr) {
    /* S2MM 起始地址寄存器（每个 slot 偏移 4 字节）*/
    vdma_write(ch, 0xAC + slot * 4, (u32)addr);
    if (sizeof(dma_addr_t) > 4)
        vdma_write(ch, 0xAC + slot * 4 + 4, (u32)(addr >> 32));
}

static void vdma_start(struct traffic_video_ch *ch) {
    u32 stride = FRAME_WIDTH;  /* NV12：Y 行步长 = 宽度 */
    vdma_write(ch, VDMA_S2MM_FRMSTORE, NUM_BUFS);
    vdma_write(ch, VDMA_S2MM_HSIZE, stride);
    /* 写 VSIZE 触发传输 */
    vdma_write(ch, VDMA_S2MM_VSIZE, FRAME_HEIGHT * 3 / 2);
    vdma_write(ch, VDMA_S2MM_CR,
               VDMA_CR_RUN | VDMA_CR_IRQEN_FRM | VDMA_CR_FRMCNT_EN);
}

static void vdma_stop(struct traffic_video_ch *ch) {
    u32 cr = vdma_read(ch, VDMA_S2MM_CR);
    vdma_write(ch, VDMA_S2MM_CR, cr & ~VDMA_CR_RUN);
}

/* ── 帧完成中断处理 ────────────────────────────────────────── */
static irqreturn_t traffic_video_isr(int irq, void *dev_id) {
    struct traffic_video_ch *ch = dev_id;
    unsigned long flags;
    u32 sr;

    sr = vdma_read(ch, VDMA_S2MM_SR);
    if (!(sr & BIT(12))) return IRQ_NONE;  /* 非帧完成中断 */

    /* 清除中断标志 */
    vdma_write(ch, VDMA_S2MM_SR, sr);

    spin_lock_irqsave(&ch->irq_lock, flags);
    if (ch->active_buf) {
        struct traffic_buf *buf = ch->active_buf;
        ch->active_buf = NULL;
        ch->frame_count++;
        /* 标记缓冲区完成，通知 V4L2 框架 */
        buf->vb.vb2_buf.timestamp = ktime_get_ns();
        buf->vb.sequence = ch->frame_count;
        buf->vb.field = V4L2_FIELD_NONE;
        vb2_buffer_done(&buf->vb.vb2_buf, VB2_BUF_STATE_DONE);

        /* 从队列中取下一帧 */
        if (!list_empty(&ch->buf_list)) {
            buf = list_first_entry(&ch->buf_list, struct traffic_buf, list);
            list_del(&buf->list);
            ch->active_buf = buf;
            /* 更新 VDMA 目标地址 */
            vdma_set_frame_addr(ch, 0, buf->dma_addr);
        }
    }
    spin_unlock_irqrestore(&ch->irq_lock, flags);

    return IRQ_HANDLED;
}

/* ── VB2 操作（缓冲区管理）────────────────────────────────── */
static int queue_setup(struct vb2_queue *q,
                       unsigned int *nbuffers, unsigned int *nplanes,
                       unsigned int sizes[], struct device *alloc_devs[]) {
    *nbuffers = max_t(unsigned int, *nbuffers, NUM_BUFS);
    *nplanes  = 1;
    sizes[0]  = FRAME_WIDTH * FRAME_HEIGHT * 3 / 2;  /* NV12 */
    return 0;
}

static int buf_prepare(struct vb2_buffer *vb) {
    if (vb2_plane_size(vb, 0) < FRAME_WIDTH * FRAME_HEIGHT * 3 / 2)
        return -EINVAL;
    vb2_set_plane_payload(vb, 0, FRAME_WIDTH * FRAME_HEIGHT * 3 / 2);
    return 0;
}

static void buf_queue(struct vb2_buffer *vb) {
    struct vb2_v4l2_buffer *vbuf = to_vb2_v4l2_buffer(vb);
    struct traffic_buf *buf = container_of(vbuf, struct traffic_buf, vb);
    struct traffic_video_ch *ch = vb2_get_drv_priv(vb->vb2_queue);
    unsigned long flags;

    buf->dma_addr = vb2_dma_contig_plane_dma_addr(vb, 0);

    spin_lock_irqsave(&ch->irq_lock, flags);
    if (!ch->active_buf) {
        ch->active_buf = buf;
        vdma_set_frame_addr(ch, 0, buf->dma_addr);
    } else {
        list_add_tail(&buf->list, &ch->buf_list);
    }
    spin_unlock_irqrestore(&ch->irq_lock, flags);
}

static int start_streaming(struct vb2_queue *q, unsigned int count) {
    struct traffic_video_ch *ch = vb2_get_drv_priv(q);
    ch->streaming = true;
    vdma_start(ch);
    return 0;
}

static void stop_streaming(struct vb2_queue *q) {
    struct traffic_video_ch *ch = vb2_get_drv_priv(q);
    vdma_stop(ch);
    ch->streaming = false;
    /* 归还所有缓冲区 */
    struct traffic_buf *buf, *tmp;
    list_for_each_entry_safe(buf, tmp, &ch->buf_list, list) {
        list_del(&buf->list);
        vb2_buffer_done(&buf->vb.vb2_buf, VB2_BUF_STATE_ERROR);
    }
    if (ch->active_buf) {
        vb2_buffer_done(&ch->active_buf->vb.vb2_buf, VB2_BUF_STATE_ERROR);
        ch->active_buf = NULL;
    }
}

static const struct vb2_ops traffic_vb2_ops = {
    .queue_setup     = queue_setup,
    .buf_prepare     = buf_prepare,
    .buf_queue       = buf_queue,
    .start_streaming = start_streaming,
    .stop_streaming  = stop_streaming,
    .wait_prepare    = vb2_ops_wait_prepare,
    .wait_finish     = vb2_ops_wait_finish,
};

/* ── V4L2 IOCTL ─────────────────────────────────────────────── */
static int vidioc_querycap(struct file *f, void *priv,
                           struct v4l2_capability *cap) {
    struct traffic_video_ch *ch = video_drvdata(f);
    strscpy(cap->driver, DRIVER_NAME, sizeof(cap->driver));
    snprintf(cap->card, sizeof(cap->card), "Traffic Cam CH%d", ch->channel);
    cap->capabilities = V4L2_CAP_VIDEO_CAPTURE | V4L2_CAP_STREAMING;
    return 0;
}

static int vidioc_g_fmt(struct file *f, void *priv, struct v4l2_format *fmt) {
    fmt->type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fmt->fmt.pix.width        = FRAME_WIDTH;
    fmt->fmt.pix.height       = FRAME_HEIGHT;
    fmt->fmt.pix.pixelformat  = FRAME_FORMAT;
    fmt->fmt.pix.field        = V4L2_FIELD_NONE;
    fmt->fmt.pix.bytesperline = FRAME_WIDTH;
    fmt->fmt.pix.sizeimage    = FRAME_WIDTH * FRAME_HEIGHT * 3 / 2;
    fmt->fmt.pix.colorspace   = V4L2_COLORSPACE_REC709;
    return 0;
}

static const struct v4l2_ioctl_ops traffic_ioctl_ops = {
    .vidioc_querycap      = vidioc_querycap,
    .vidioc_g_fmt_vid_cap = vidioc_g_fmt,
    .vidioc_s_fmt_vid_cap = vidioc_g_fmt,  /* 固定格式，忽略设置 */
    .vidioc_try_fmt_vid_cap = vidioc_g_fmt,
    .vidioc_reqbufs       = vb2_ioctl_reqbufs,
    .vidioc_querybuf      = vb2_ioctl_querybuf,
    .vidioc_qbuf          = vb2_ioctl_qbuf,
    .vidioc_dqbuf         = vb2_ioctl_dqbuf,
    .vidioc_streamon      = vb2_ioctl_streamon,
    .vidioc_streamoff     = vb2_ioctl_streamoff,
};

/* ── platform_driver probe ─────────────────────────────────── */
static int traffic_video_probe(struct platform_device *pdev) {
    struct device *dev = &pdev->dev;
    struct traffic_video_ch *ch;
    int channel_id, ret;

    if (of_property_read_u32(dev->of_node, "xlnx,channel-id", &channel_id))
        return -EINVAL;
    if (channel_id >= NUM_CHANNELS) return -EINVAL;

    ch = devm_kzalloc(dev, sizeof(*ch), GFP_KERNEL);
    if (!ch) return -ENOMEM;

    ch->channel  = channel_id;
    ch->vdma_base = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(ch->vdma_base)) return PTR_ERR(ch->vdma_base);

    ch->irq = platform_get_irq(pdev, 0);
    if (ch->irq < 0) return ch->irq;

    mutex_init(&ch->lock);
    spin_lock_init(&ch->irq_lock);
    INIT_LIST_HEAD(&ch->buf_list);

    ret = devm_request_irq(dev, ch->irq, traffic_video_isr,
                           IRQF_SHARED, DRIVER_NAME, ch);
    if (ret) return ret;

    /* 注册 V4L2 设备 */
    ret = v4l2_device_register(dev, &ch->v4l2_dev);
    if (ret) return ret;

    /* 初始化 VB2 队列 */
    ch->queue.type            = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    ch->queue.io_modes        = VB2_DMABUF | VB2_MMAP;
    ch->queue.drv_priv        = ch;
    ch->queue.buf_struct_size = sizeof(struct traffic_buf);
    ch->queue.ops             = &traffic_vb2_ops;
    ch->queue.mem_ops         = &vb2_dma_contig_memops;
    ch->queue.timestamp_flags = V4L2_BUF_FLAG_TIMESTAMP_MONOTONIC;
    ch->queue.lock            = &ch->lock;
    ch->queue.dev             = dev;
    ret = vb2_queue_init(&ch->queue);
    if (ret) goto unreg_v4l2;

    /* 注册 video_device */
    snprintf(ch->vdev.name, sizeof(ch->vdev.name),
             "traffic-cam-%d", channel_id);
    ch->vdev.v4l2_dev = &ch->v4l2_dev;
    ch->vdev.fops     = &vb2_fops;
    ch->vdev.ioctl_ops= &traffic_ioctl_ops;
    ch->vdev.release  = video_device_release_empty;
    ch->vdev.queue    = &ch->queue;
    ch->vdev.lock     = &ch->lock;
    video_set_drvdata(&ch->vdev, ch);

    ret = video_register_device(&ch->vdev, VFL_TYPE_VIDEO, -1);
    if (ret) goto unreg_v4l2;

    g_channels[channel_id] = ch;
    platform_set_drvdata(pdev, ch);
    dev_info(dev, "Channel %d → /dev/video%d\n",
             channel_id, ch->vdev.num);
    return 0;

unreg_v4l2:
    v4l2_device_unregister(&ch->v4l2_dev);
    return ret;
}

static int traffic_video_remove(struct platform_device *pdev) {
    struct traffic_video_ch *ch = platform_get_drvdata(pdev);
    video_unregister_device(&ch->vdev);
    v4l2_device_unregister(&ch->v4l2_dev);
    return 0;
}

static const struct of_device_id traffic_video_of_ids[] = {
    { .compatible = "traffic-edge,video-capture" },
    {}
};
MODULE_DEVICE_TABLE(of, traffic_video_of_ids);

static struct platform_driver traffic_video_driver = {
    .probe  = traffic_video_probe,
    .remove = traffic_video_remove,
    .driver = {
        .name           = DRIVER_NAME,
        .of_match_table = traffic_video_of_ids,
    },
};
module_platform_driver(traffic_video_driver);

MODULE_AUTHOR("Traffic Edge Team");
MODULE_DESCRIPTION("ZCU102 Traffic Surveillance V4L2 Driver");
MODULE_LICENSE("GPL v2");
