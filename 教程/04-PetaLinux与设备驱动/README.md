# 阶段 4：PetaLinux 与 Linux 设备驱动

## 学习目标

- 使用 PetaLinux 2023.1 构建完整 Linux 系统（内核 + rootfs + BOOT.BIN）
- 理解 Device Tree 与 Device Tree Overlay
- 编写用户空间 UIO 驱动访问 PL 外设
- 编写内核空间字符设备驱动（platform_driver）
- 使用 V4L2 框架访问视频设备

---

## 4.1 PetaLinux 工作流程

```
XSA 文件
    │
    ▼
petalinux-create   →  创建工程
    │
    ▼
petalinux-config   →  配置 HW（导入 XSA）、内核、rootfs
    │
    ▼
petalinux-build    →  编译 U-Boot / 内核 / rootfs（Yocto）
    │
    ▼
petalinux-package  →  生成 BOOT.BIN / image.ub / rootfs.ext4
    │
    ▼
烧录 SD 卡 → 板卡启动
```

---

## 4.2 实验 4-1：最小化 PetaLinux 系统构建

```bash
# 1. 创建工程（基于 ZCU102 模板）
petalinux-create --type project --template zynqMP \
    --name zcu102_linux

cd zcu102_linux

# 2. 导入 XSA
petalinux-config --get-hw-description=../vivado/zcu102.xsa

# 3. 配置内核（选择必要模块）
petalinux-config -c kernel
# 确保以下选项开启：
# CONFIG_XILINX_DMA=y
# CONFIG_CAN=y, CONFIG_CAN_XILINXCAN=y
# CONFIG_MEDIA_SUPPORT=y, CONFIG_VIDEO_V4L2=y

# 4. 配置 rootfs（添加工具）
petalinux-config -c rootfs
# 添加：packagegroup-petalinux-utils
#       python3, python3-numpy, canutils

# 5. 构建（约 1-3 小时，取决于机器性能）
petalinux-build

# 6. 打包
petalinux-package --boot \
    --fsbl ./images/linux/zynqmp_fsbl.elf \
    --u-boot \
    --pmufw \
    --fpga ../vivado/zcu102.bit \
    --force
```

---

## 4.3 Device Tree 基础

### 4.3.1 查看生成的 DT

```bash
# 生成后在以下位置：
cat components/plnx_workspace/device-tree/device-tree/pl.dtsi
```

### 4.3.2 自定义 DT 节点（user_custompl.dtsi）

```dts
/* 为自定义 AXI 外设添加 DT 节点 */
&amba_pl {
    my_custom_ip: my_custom_ip@A0000000 {
        compatible = "xlnx,my-custom-ip-1.0";
        reg = <0x0 0xA0000000 0x0 0x10000>;
        interrupt-parent = <&gic>;
        interrupts = <0 89 4>;      /* SPI 89 = PL IRQ[0] + 68 偏移 */
        clocks = <&misc_clk_0>;
    };
};
```

### 4.3.3 Device Tree Overlay（热插拔 PL 外设）

```dts
/* my_overlay.dts */
/dts-v1/;
/plugin/;

&fpga_region0 {
    #address-cells = <2>;
    #size-cells = <2>;

    firmware-name = "my_design.bit.bin";

    my_custom_ip: my_custom_ip@A0000000 {
        compatible = "xlnx,my-custom-ip-1.0";
        reg = <0x0 0xA0000000 0x0 0x10000>;
    };
};
```

```bash
# 转换并加载 Overlay
dtc -I dts -O dtb -o my_overlay.dtbo my_overlay.dts
mkdir -p /sys/kernel/config/device-tree/overlays/my_overlay
cp my_overlay.dtbo /sys/kernel/config/device-tree/overlays/my_overlay/
echo 1 > /sys/kernel/config/device-tree/overlays/my_overlay/status
```

---

## 4.4 实验 4-2：UIO 用户空间驱动

对于简单 PL 外设，UIO 是最快的访问方式，无需编写内核驱动。

```c
// uio_example.c - 通过 UIO 访问 AXI GPIO
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

#define UIO_DEV     "/dev/uio0"
#define MAP_SIZE    0x10000

int main() {
    int fd = open(UIO_DEV, O_RDWR);
    if (fd < 0) { perror("open"); return 1; }

    volatile uint32_t *reg = mmap(NULL, MAP_SIZE,
        PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (reg == MAP_FAILED) { perror("mmap"); return 1; }

    // AXI GPIO 寄存器偏移（PG144）
    // 0x000: GPIO_DATA, 0x004: GPIO_TRI
    reg[1] = 0x00000000;  // 全部输出
    for (int i = 0; ; i++) {
        reg[0] = 1 << (i % 8);
        usleep(200000);
    }

    munmap((void*)reg, MAP_SIZE);
    close(fd);
    return 0;
}
```

DT 中启用 UIO：
```dts
axi_gpio_0: gpio@a0000000 {
    compatible = "generic-uio";  /* 使用通用 UIO 驱动 */
    reg = <0x0 0xa0000000 0x0 0x10000>;
};
```

---

## 4.5 实验 4-3：内核 Platform 驱动

```c
// my_driver.c - 最小化 platform_driver 框架
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/io.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>

#define DRIVER_NAME "my_custom_ip"

struct my_dev {
    void __iomem *base;
    struct cdev  cdev;
    dev_t        devnum;
};

static int my_probe(struct platform_device *pdev) {
    struct my_dev *priv;
    struct resource *res;

    priv = devm_kzalloc(&pdev->dev, sizeof(*priv), GFP_KERNEL);
    res  = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    priv->base = devm_ioremap_resource(&pdev->dev, res);

    platform_set_drvdata(pdev, priv);
    dev_info(&pdev->dev, "probed at %pa, size %#x\n",
             &res->start, (u32)resource_size(res));
    return 0;
}

static int my_remove(struct platform_device *pdev) {
    dev_info(&pdev->dev, "removed\n");
    return 0;
}

static const struct of_device_id my_of_match[] = {
    { .compatible = "xlnx,my-custom-ip-1.0" },
    {},
};
MODULE_DEVICE_TABLE(of, my_of_match);

static struct platform_driver my_driver = {
    .probe  = my_probe,
    .remove = my_remove,
    .driver = {
        .name           = DRIVER_NAME,
        .of_match_table = my_of_match,
    },
};
module_platform_driver(my_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("ZCU102 Tutorial");
MODULE_DESCRIPTION("Custom AXI IP Platform Driver");
```

---

## 4.6 V4L2 与 MIPI CSI-2

ZCU102 支持通过 Xilinx Video IP 套件接入 MIPI CSI-2 摄像头：

```bash
# 查看 V4L2 设备
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext

# 抓帧测试
v4l2-ctl -d /dev/video0 \
    --set-fmt-video=width=1920,height=1080,pixelformat=NV12 \
    --stream-mmap=3 \
    --stream-to=/tmp/frame.yuv \
    --stream-count=1
```

---

## 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| PetaLinux 工具参考 | UG1144 | 完整 PetaLinux 命令手册 |
| Vitis Embedded Tutorials | [github.com/Xilinx/Vitis-Tutorials/Embedded_Software](https://github.com/Xilinx/Vitis-Tutorials/tree/master/Embedded_Software) | 嵌入式 Linux 教程 |
| Linux 设备驱动开发 | UG1186 | Xilinx Linux 驱动开发指南 |
| Xilinx Linux 内核 | [github.com/Xilinx/linux-xlnx](https://github.com/Xilinx/linux-xlnx) | 官方内核源码 |
| Xilinx embeddedsw | [github.com/Xilinx/embeddedsw](https://github.com/Xilinx/embeddedsw) | 裸机驱动库 |
| DT Overlay 指南 | 内核文档 Documentation/devicetree/overlay-notes.rst | DT Overlay 规范 |

详见 [`refs/`](refs/) 目录。
