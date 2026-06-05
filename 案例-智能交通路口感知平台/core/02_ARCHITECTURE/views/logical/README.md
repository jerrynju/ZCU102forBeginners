# 逻辑视图

> 4+1 视图中的核心视图，关注 **模块、接口、关系**。

## 系统总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ZCU102 边缘感知盒                             │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PL（FPGA 逻辑区）                          │   │
│  │                                                              │   │
│  │  Camera[0..3]                                                │   │
│  │  MIPI CSI-2 ──► ISP-HLS ──► AXI-Stream ──►┐                │   │
│  │                 (去马赛克/                  │                │   │
│  │                  降噪/resize)               ▼                │   │
│  │                                      Video-DMA              │   │
│  │  USB3 Camera ──► UVC Capture ─────────────►│                │   │
│  │                                            │                │   │
│  │            ┌───────────────────────────────┘                │   │
│  │            ▼                                                │   │
│  │       DDR4 Frame Buffer (4GB)                               │   │
│  │            │                                                │   │
│  │            ▼                                                │   │
│  │   DPU (B4096) ◄─── AXI-HP ─── Weight BRAM                 │   │
│  │  (AI推理引擎)                                                │   │
│  │            │                                                │   │
│  │            ▼                                                │   │
│  │   OSD Overlay ──► DisplayPort TX ──► 本地监视器              │   │
│  │                                                              │   │
│  │   10GbE MAC (PL) ──► GTH Transceiver ──► 光口               │   │
│  │   CAN Controller ──► RS-485 ──► 信号灯控制器                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          AXI Interconnect                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PS（ARM 处理器区）                         │   │
│  │                                                              │   │
│  │  Cortex-A53 × 4  (PetaLinux)                                │   │
│  │  ├── Vitis AI Runtime (VART)  ← DPU 调度与结果解析           │   │
│  │  ├── 目标跟踪 (DeepSORT/ByteTrack)                           │   │
│  │  ├── 车牌 OCR (CRNN)                                         │   │
│  │  ├── 事件检测 (越线/逆行/拥堵)                                │   │
│  │  ├── MQTT Client → 城市云平台                                │   │
│  │  ├── gRPC Server → 管理控制台                                │   │
│  │  └── REST API + WebSocket → 本地 Web UI                      │   │
│  │                                                              │   │
│  │  Cortex-R5 × 2  (FreeRTOS) ← OpenAMP 与 A53 通信            │   │
│  │  ├── 信号灯实时控制状态机                                     │   │
│  │  ├── CAN 总线收发                                            │   │
│  │  ├── 硬件看门狗 / 故障安全                                    │   │
│  │  └── 车辆计数脉冲中断处理                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## 模块关系

| 模块 | 上游 | 下游 | 通信方式 |
|------|------|------|----------|
| MIPI RX | 摄像头 | ISP | AXI-Stream |
| ISP | MIPI RX | VDMA | AXI-Stream |
| VDMA | ISP | DDR | AXI |
| DPU | DDR | PS | AXI |
| OSD | DDR, 检测结果 | DP | AXI-Stream |
| 10GbE | PS, R5 | 云端 | AXI |
| CAN | R5 | 信号灯 | GPIO |
| VART (PS) | DPU | 跟踪 | 共享内存 |
| 跟踪 | VART | 事件检测 | 内存 |
| 事件检测 | 跟踪 | MQTT/REST | 内存 |
| MQTT | 事件 | 云端 | TCP/TLS |
| OpenAMP | PS | R5 | RPMsg |

## 关键接口

- ICD-001: PS↔PL 共享内存 (DetectionResult)
- ICD-002: R5↔A53 RPMsg
- ICD-003: MQTT 主题
- ICD-004: gRPC 管理接口
- ICD-005: CAN 总线帧
- ICD-006: OSD 寄存器

## 详细分解

参见 [decomposition/](../decomposition/)：
- [DES-ARCH-001: PS/PL 划分](../decomposition/DES-ARCH-001-ps-pl-split.md)
- [DES-ARCH-004: 主控线程模型](../decomposition/DES-ARCH-004-thread-model.md)
- [DES-ARCH-005: R5 FreeRTOS 任务](../decomposition/DES-ARCH-005-r5-tasks.md)
