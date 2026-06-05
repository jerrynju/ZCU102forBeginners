---
id: glossary.md
title: 术语表
type: glossary
status: active
version: 1.0.0
---

# 术语表

## 硬件术语

| 术语 | 英文 | 说明 |
|------|------|------|
| ZCU102 | Zynq UltraScale+ MPSoC 评估板 | Xilinx 推出的 MPSOC 评估板，搭载 XCZU9EG |
| MPSOC | Multi-Processor System on Chip | 多核异构系统级芯片，集成 ARM + FPGA |
| PL | Programmable Logic | FPGA 逻辑区 |
| PS | Processing System | ARM 处理器子系统（A53 + R5） |
| A53 | Cortex-A53 | 应用处理器，运行 Linux |
| R5  | Cortex-R5  | 实时处理器，运行 FreeRTOS |
| DPU | Deep Processing Unit | Xilinx FPGA 上的 AI 推理 IP |
| ISP  | Image Signal Processor | 图像信号处理（去马赛克/降噪/白平衡等） |
| OSD  | On-Screen Display | 视频上叠加文字/边框 |
| HLS  | High-Level Synthesis | 高层次综合（C/C++ → RTL） |
| BD   | Block Design | Vivado 图形化 IP 集成设计 |
| XDC  | Xilinx Design Constraints | 时序/引脚约束文件 |
| D-PHY| MIPI 物理层 | MIPI CSI-2 摄像头物理接口 |
| GTH  | Gigabit Transceiver | Xilinx 高速串行收发器 |
| AXI  | Advanced eXtensible Interface | ARM 高速总线协议族 |
| VDMA | Video Direct Memory Access | 视频帧直接内存访问 IP |
| eFUSE | 电子熔丝 | 一次性可编程存储，用于安全密钥 |
| BBRAM | Battery-Backed RAM | 电池备份 RAM，存加密密钥 |
| PMU   | Platform Management Unit | MPSOC 平台管理单元 |
| ATF   | ARM Trusted Firmware | ARM 信任固件（EL3） |
| FSBL  | First Stage Bootloader | Zynq 第一阶段引导 |

## 软件/算法术语

| 术语 | 英文 | 说明 |
|------|------|------|
| VART | Vitis AI Runtime | Xilinx AI 推理运行时 |
| DPUCZDx8G | — | ZCU102 DPU 的 IP 核代号 |
| PTQ   | Post-Training Quantization | 训练后量化 |
| QAT   | Quantization-Aware Training | 量化感知训练 |
| mAP   | mean Average Precision | 目标检测平均精度 |
| MOTA  | Multi-Object Tracking Accuracy | 多目标跟踪精度 |
| NMS   | Non-Maximum Suppression | 非极大值抑制 |
| CTC   | Connectionist Temporal Classification | 序列识别损失函数 |
| CRNN  | CNN+RNN+CTC | 经典车牌/OCR 架构 |
| LPRNet| License Plate Recognition Net | 端到端车牌识别网络 |
| ByteTrack | — | 高效多目标跟踪算法（字节跳动） |
| YOLO  | You Only Look Once | 实时目标检测模型系列 |
| INT8  | 8-bit Integer | 低精度整型推理 |
| xmodel | — | Vitis AI 编译后的 DPU 模型格式 |
| OpenAMP | Asymmetric Multi-Processing | 异构多处理框架 |
| RPMsg | Remote Processor Messaging | 核间通信消息协议 |
| MQTT  | Message Queuing Telemetry Transport | IoT 消息协议 |
| gRPC  | — | Google 高性能 RPC 框架 |
| Protobuf | Protocol Buffers | Google 序列化协议 |
| TLS   | Transport Layer Security | 传输层安全协议 |
| mTLS  | Mutual TLS | 双向 TLS 认证 |
| OTA   | Over-The-Air | 远程升级 |
| SWUpdate | — | Linux OTA 框架 |

## 项目内部术语

| 术语 | 含义 |
|------|------|
| EdgeVision-T1 | 产品名（路口感知终端） |
| FCT | Functional Circuit Test（工厂功能测试） |
| 算法黄金参考 | 03_ALGORITHM/golden-ref 中的固定基准 |
| 追溯矩阵 | traceability.yml 中的双向链接 |
| 核心部分 | core/ 目录（纯文本） |
| 工具流 | tools/ 目录（可迁移自动化） |
