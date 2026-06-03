# 阶段 7：高速接口与串行协议

## 学习目标

- 理解 GTH Transceiver 架构与 SerDes 原理
- 配置 10 Gigabit Ethernet MAC（CMAC）子系统
- 实现 MIPI CSI-2 4-lane 摄像头接口
- 配置 AXI CAN（500 Kbps）并测试帧收发
- 了解 PCIe Gen3×4 端点实现要点

---

## 7.1 ZCU102 高速接口资源

| 接口 | 数量 | 最高速率 | 位置 |
|------|------|---------|------|
| GTH Transceiver | 16 | 16.375 Gbps/lane | PL |
| CMAC (10GbE) | 1 | 10 Gbps | PL |
| PCIe Gen3×4 | 1 | 4×8Gbps | PL |
| MIPI CSI-2 | 1 (PS) | 4-lane 1.5Gbps | PS |
| PS-GEM (GbE) | 4 | 1 Gbps | PS |
| AXI CAN | 2 | 1 Mbps | PS |
| USB 3.0 | 2 | 5 Gbps | PS |

---

## 7.2 实验 7-1：GTH 10GbE（CMAC）

### 7.2.1 Block Design 关键组件

```
SFP+ 光口 (J13/J14)
    │  GTH Lane 0/1 (TX/RX)
    ▼
CMAC Subsystem (PG203)
    │  AXI4-Stream (64-bit @ 390MHz)
    ▼
AXI 10G Ethernet (PG157) 或 直接 DMA
    │
    ▼
PS HP 接口 → DDR4
```

### 7.2.2 CMAC IP 配置

```tcl
# 10GbE CMAC 配置
create_bd_cell -type ip -vlnv xilinx.com:ip:cmac_usplus:3.1 cmac_usplus_0
set_property -dict [list \
    CONFIG.CMAC_CAUI4_MODE     {0}        \
    CONFIG.NUM_LANES           {1x10G}    \
    CONFIG.GT_REF_CLK_FREQ     {156.25}   \
    CONFIG.USER_INTERFACE      {AXIS}     \
    CONFIG.INCLUDE_RS_FEC      {0}        \
    CONFIG.LANE1_GT_LOC        {X0Y8}     \
] [get_bd_cells cmac_usplus_0]
```

### 7.2.3 约束（GTH 参考时钟 + 位置）

```xdc
# GTH 参考时钟（156.25 MHz for 10GbE）
set_property PACKAGE_PIN V7 [get_ports gt_ref_clk_p]
set_property PACKAGE_PIN V6 [get_ports gt_ref_clk_n]

# GTH RX/TX（SFP+ Lane 0）
set_property LOC GTHE4_CHANNEL_X0Y8 [get_cells */gt_usrclk_source/channel_inst]
```

### 7.2.4 简单 AXI-Stream 环回测试

```c
// 10GbE AXI-Stream 环回（Standalone C 代码）
#include "xaxiethernet.h"
#include "xaxidma.h"

// 发送 64 字节 UDP 帧
u8 tx_buf[64] = {
    // Ethernet Header (DA:FF:FF:FF:FF:FF, SA:00:0A:35:01:02:03)
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0x00,0x0A,0x35,0x01,0x02,0x03,
    0x08,0x00,  // EtherType: IPv4
    // ... UDP payload
};
XAxiDma_SimpleTransfer(&dma, (u32)tx_buf, 64, XAXIDMA_DMA_TO_DEVICE);
while (XAxiDma_Busy(&dma, XAXIDMA_DMA_TO_DEVICE));
```

---

## 7.3 实验 7-2：MIPI CSI-2 摄像头

### 7.3.1 CSI-2 接收链路

```
Camera (MIPI CSI-2 4-lane, 1080p30)
    │ MIPI D-PHY (PS MIPI RX)
    ▼
Xilinx MIPI CSI-2 RX Subsystem (PG232)
    │ AXI4-Stream (RAW10)
    ▼
Demosaic IP (PG286)
    │ RGB 3×8-bit
    ▼
Gamma LUT / Color Convert
    │ YCbCr 4:2:2
    ▼
Video Frame Buffer Write (PG278)
    │ AXI4 (写入 DDR)
    ▼
V4L2 /dev/video0 (PetaLinux)
```

### 7.3.2 关键 IP 配置

```tcl
# MIPI CSI-2 RX 子系统（ZCU102 PS MIPI 接口）
create_bd_cell -type ip \
    -vlnv xilinx.com:ip:mipi_csi2_rx_subsystem:5.2 mipi_csi2_rx_ss_0
set_property -dict [list \
    CONFIG.CMN_NUM_LANES       {4}     \
    CONFIG.CMN_PXL_FORMAT      {RAW10} \
    CONFIG.CMN_VC_SUPPORT      {1}     \
    CONFIG.SupportLevel        {1}     \
    CONFIG.DPY_LINE_RATE       {1500}  \
    CONFIG.CMN_INC_VFB         {1}     \
] [get_bd_cells mipi_csi2_rx_ss_0]
```

### 7.3.3 V4L2 用户空间访问

```bash
# 在 PetaLinux 上
v4l2-ctl -d /dev/video0 \
    --set-fmt-video=width=1920,height=1080,pixelformat=NV12 \
    --stream-mmap=4 --stream-skip=30 \
    --stream-to=/tmp/capture.yuv --stream-count=10

# 确认帧率
v4l2-ctl -d /dev/media0 --get-subdev-fmt pad=0
media-ctl --print-topology
```

---

## 7.4 实验 7-3：AXI CAN 通信

### 7.4.1 Hardware（PS 内置 CAN0/CAN1）

```dts
/* ZCU102 DT：CAN0 已在 PS 内，只需 pinmux */
&can0 {
    status = "okay";
    /* 引脚分配：MIO 38(TX), MIO 39(RX) */
};
```

### 7.4.2 Linux SocketCAN

```bash
# 配置 CAN 总线（500 Kbps）
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# 发送 CAN 帧（ID=0x101, 数据=01 1E 01 00）
cansend can0 101#011E0100

# 接收（监听）
candump can0

# 负载测试
cangen can0 -g 5 -I 0x101 -L 8 -D i &
canstat can0
```

### 7.4.3 C SocketCAN API

```c
// can_send.c - SocketCAN 发送信号灯状态帧
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/socket.h>

int sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);
struct ifreq ifr;
strcpy(ifr.ifr_name, "can0");
ioctl(sock, SIOCGIFINDEX, &ifr);

struct sockaddr_can addr = {
    .can_family  = AF_CAN,
    .can_ifindex = ifr.ifr_ifindex,
};
bind(sock, (struct sockaddr*)&addr, sizeof(addr));

struct can_frame frame = {
    .can_id  = 0x101,
    .can_dlc = 4,
    .data    = {0x00, 0x1E, 0x01, 0x00},  // NS_GREEN 30s 自适应
};
write(sock, &frame, sizeof(frame));
```

---

## 7.5 PCIe Gen3×4 端点（概念）

ZCU102 PL 集成 PCIe Hard IP，支持端点模式（Endpoint Mode）：

```tcl
# PCIe 端点配置
create_bd_cell -type ip -vlnv xilinx.com:ip:pcie4_uscale_plus:1.3 pcie4_uscale_plus_0
set_property -dict [list \
    CONFIG.PL_LINK_CAP_MAX_LINK_SPEED {8.0_GT/s}  \
    CONFIG.PL_LINK_CAP_MAX_LINK_WIDTH {X4}         \
    CONFIG.axisten_if_width            {256_bit}   \
    CONFIG.AXISTEN_IF_RC_STRADDLE      {true}      \
] [get_bd_cells pcie4_uscale_plus_0]
```

> **注意**：PCIe 需要专用 GTH Quad（X0Y2），参考 UG1085 第 29 章。

---

## 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| CMAC 子系统 | PG203 | 10/25/40/100GbE CMAC 产品指南 |
| MIPI CSI-2 RX | PG232 | MIPI CSI-2 接收子系统手册 |
| GTH Transceiver | UG576 | GTH 收发器用户指南 |
| AXI CAN | PG023 | AXI CAN IP 产品指南 |
| PCIe for UltraScale+ | PG213 | PCIe 端点 IP 手册 |
| SocketCAN 文档 | kernel.org/doc/html/latest/networking/can.html | Linux SocketCAN |
| ZCU102 接口教程 | [Vitis-Tutorials/Embedded_Software](https://github.com/Xilinx/Vitis-Tutorials) | 接口相关教程 |

详见 [`refs/`](refs/) 目录。
