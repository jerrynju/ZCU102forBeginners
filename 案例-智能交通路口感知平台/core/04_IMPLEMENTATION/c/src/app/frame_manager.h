#pragma once
#include <cstdint>
#include <memory>
#include <vector>
#include <mutex>
#include <condition_variable>
#include <optional>
#include <chrono>
#include <opencv2/core.hpp>

// 视频帧描述符（零拷贝设计：直接映射 PL VDMA 输出的 DDR 物理地址）
struct VideoFrame {
    int         channel;          // 摄像头通道 0-3
    uint32_t    frame_id;         // 帧序号（单调递增）
    uint64_t    timestamp_us;     // 采集时间戳（来自 R5 GPS PPS 同步）
    uint8_t*    data_nv12;        // NV12 数据指针（映射自 /dev/mem 或 dma-buf）
    size_t      size;             // 数据大小 = W * H * 3 / 2
    int         width, height;    // 帧分辨率

    // 懒加载：首次调用时才执行 NV12→BGR 转换（供 Web 预览或 CPU 算法使用）
    cv::Mat     bgr_preview;      // 1/4 分辨率预览图（480×270）
    bool        preview_ready{false};

    // 获取预览图（首次调用触发转换）
    const cv::Mat& get_preview();

    // 获取 JPEG 缩略图（用于事件上报，有损压缩）
    std::vector<uint8_t> to_jpeg(int quality = 70) const;

    // 禁止拷贝（帧数据通过指针引用，避免大内存拷贝）
    VideoFrame(const VideoFrame&) = delete;
    VideoFrame& operator=(const VideoFrame&) = delete;
    VideoFrame(VideoFrame&&) = default;
};

// 每通道三重缓冲管理器
// PL VDMA 写入空闲缓冲 → 完成后通知 → 应用层取走处理 → 归还
class ChannelBuffer {
public:
    static constexpr int NUM_BUFS = 3;

    explicit ChannelBuffer(int ch, uint8_t* base_addr, size_t frame_size);

    // VDMA 中断触发：标记某个缓冲区已就绪
    void mark_ready(int buf_idx, uint64_t timestamp_us, uint32_t frame_id);

    // 应用层拿走最新帧（阻塞，超时返回 nullptr）
    std::shared_ptr<VideoFrame> pop(int timeout_ms = 50);

    // 返回最新帧（不阻塞，没有则返回 nullptr）
    std::shared_ptr<VideoFrame> try_pop();

    // 获取最新帧（不消费，用于 Web 预览）
    std::shared_ptr<VideoFrame> peek_latest();

    int get_channel() const { return channel_; }
    uint64_t get_drop_count() const { return drop_count_; }

private:
    int channel_;
    uint8_t* base_addr_;
    size_t   frame_size_;
    uint64_t drop_count_{0};

    struct BufSlot {
        uint8_t* ptr;
        bool     ready{false};
        uint32_t frame_id{0};
        uint64_t timestamp_us{0};
    };
    BufSlot slots_[NUM_BUFS];

    std::shared_ptr<VideoFrame> latest_;
    std::mutex  mtx_;
    std::condition_variable cv_;
};

// 全局帧管理器（管理 4 个通道）
class FrameManager {
public:
    explicit FrameManager(int num_channels);
    ~FrameManager();

    // 推送就绪帧（由 V4L2 驱动回调或 VDMA 中断调用）
    void push(int channel, uint8_t* data, uint64_t ts_us, uint32_t frame_id);

    // 推理线程：按通道取帧
    std::shared_ptr<VideoFrame> pop(int channel, int timeout_ms = 50);

    // Web 预览：取最新帧
    std::shared_ptr<VideoFrame> get_latest(int channel);

    // 统计
    void print_stats() const;

private:
    int num_channels_;
    std::vector<std::unique_ptr<ChannelBuffer>> channels_;

    // 物理内存映射（reserved-memory 区域）
    int      mem_fd_{-1};
    uint8_t* mem_base_{nullptr};
    static constexpr size_t FRAME_SIZE = 1920 * 1080 * 3 / 2;  // NV12 1080p
    static constexpr uintptr_t VBUF_BASE = 0x80000000UL;       // 与设备树对齐
};
