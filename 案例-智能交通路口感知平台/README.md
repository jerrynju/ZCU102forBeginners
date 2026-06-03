# 智能交通路口多模态感知与边缘计算平台

> 基于 Xilinx ZCU102（Zynq UltraScale+ MPSoC）的商业级参考案例  
> 覆盖深度学习推理 / 高速视频传输 / 实时控制 / 云边协同全栈开发

---

## 商业背景

全球智慧交通市场规模 2024 年超过 **380 亿美元**，预计 2030 年达到 **980 亿美元**（CAGR 17%）。
路口感知是智慧城市最高频的部署节点，每个城市路口需要一套融合感知、分析、控制于一体的边缘计算单元。

**本案例** 设计一套路口边缘感知盒，可接入 4 路摄像头，完成实时目标检测、车牌识别、
流量统计、违规事件上报，并通过 10GbE 与城市交通云平台对接，通过 CAN 总线控制信号灯。

---

## 系统全局架构

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

外部连接：
  4× MIPI Camera (Sony IMX415, 4K@30fps)
  1× USB3.0 Camera (备用/热插拔)
  1× 10GbE 光口 → 城市云平台
  1× DisplayPort → 本地运维显示器
  1× CAN Bus → 信号灯控制器
  1× GPS/GNSS → 时间同步（PPS 信号接 PL GPIO）
  1× 4G/5G 模组 (USB) → 备用回传链路
```

---

## 模块分解与技术栈

| 模块 | 实现位置 | 核心技术 | 就业热度 |
|------|---------|---------|---------|
| MIPI CSI-2 接收 | PL | Xilinx MIPI IP / 自研 Verilog | ★★★★ |
| ISP 图像信号处理 | PL (HLS) | Vitis HLS / AXI-Stream | ★★★★★ |
| 视频 DMA | PL + PS | VDMA / CDMA / AXI HP | ★★★★ |
| DPU AI 推理引擎 | PL | Vitis AI / DPU-TRD | ★★★★★ |
| OSD 字幕叠加 | PL (HLS) | AXI-Stream Video | ★★★ |
| 10GbE 网络 | PL (GTH) | XXV Ethernet IP | ★★★★ |
| CAN 控制器 | PL | AXI CAN IP | ★★★ |
| 目标检测模型 | PS (VART) | YOLOv8 量化部署 | ★★★★★ |
| 多目标跟踪 | PS (C++) | ByteTrack | ★★★★ |
| 车牌识别 | PS (VART) | LPRNet / CRNN | ★★★★ |
| 实时控制 | PS R5 (FreeRTOS) | OpenAMP / RPMsg | ★★★★ |
| 云端通信 | PS A53 (Linux) | MQTT / gRPC / TLS | ★★★★★ |
| 本地管理 | PS A53 (Linux) | REST API / WebSocket | ★★★★ |
| 安全启动 | PS Boot ROM | RSA-4096 / AES-256 | ★★★★ |
| OTA 升级 | PS A53 (Linux) | SWUpdate / A-B 分区 | ★★★★ |

---

## 子文档目录

| 文档 | 内容 |
|------|------|
| [01-需求与架构](docs/01-需求与架构.md) | 系统需求、架构决策、接口规范 |
| [02-FPGA硬件开发](docs/02-FPGA硬件开发.md) | Vivado工程、HLS IP、时序约束 |
| [03-AI模型开发](docs/03-AI模型开发.md) | 模型训练、量化、DPU部署 |
| [04-嵌入式软件开发](docs/04-嵌入式软件开发.md) | PetaLinux、驱动、应用层 |
| [05-实时控制开发](docs/05-实时控制开发.md) | FreeRTOS、CAN、OpenAMP |
| [06-云端与通信](docs/06-云端与通信.md) | MQTT、gRPC、数据协议设计 |
| [07-安全与量产](docs/07-安全与量产.md) | 安全启动、OTA、生产测试 |
| [08-商业化路径](docs/08-商业化路径.md) | 定价策略、竞品分析、客户交付 |
| [hardware/](hardware/) | Vivado 工程结构、HLS 源码 |
| [software/](software/) | Linux 应用、驱动、FreeRTOS |
| [ai/](ai/) | 模型训练脚本、量化流程 |
| [scripts/](scripts/) | 构建脚本、烧录脚本、测试脚本 |
