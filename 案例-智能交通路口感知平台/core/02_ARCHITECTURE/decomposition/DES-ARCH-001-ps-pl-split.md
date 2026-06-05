---
id: DES-ARCH-001
title: PS/PL 功能划分
type: design-architecture
status: approved
owner: architect-team
version: 1.0
traces: { up: [SYS-REQ-001, SYS-REQ-008, IF-REQ-001, IF-REQ-002, IF-REQ-004, IF-REQ-005, SAF-REQ-001, PERF-REQ-001, PERF-REQ-002], down: [MOD-RTL-MIPI-RX, MOD-HLS-ISP, MOD-RTL-XXV-ETH, MOD-C-VIDEO-DRV] }
tags: [architecture, ps-pl-split]
---

# DES-ARCH-001: PS/PL 功能划分

## 划分原则

| 类型 | 适合位置 | 理由 |
|------|---------|------|
| 大数据流并行 | PL | 软件无法承担带宽 |
| 固定计算模式 | PL (DPU) | 资源利用率高，延迟确定性 |
| 数据相关算法 | PS A53 | 灵活、易迭代 |
| 硬实时 | PS R5 | 无 Linux 调度抖动 |
| 网络协议栈 | PS A53 | Linux 提供完整栈 |
| 线速转发 | PL (GTH) | 时序确定性 |

## 决策表

| 决策点 | 选择 | 理由 |
|--------|------|------|
| ISP 图像处理 | PL (HLS) | 4 路并行需 >10 GB/s 吞吐 |
| AI 推理 | PL (DPU) | 固定计算模式，利用率 > 90% |
| 目标跟踪 | PS A53 | 数据相关，软件灵活 |
| 信号灯控制 | PS R5 | 硬实时 < 10ms |
| 网络协议栈 | PS A53 | 完整 TCP/IP + TLS |
| 10GbE MAC | PL (GTH) | 线速转发 |

## 资源分配（ZCU102 XCZU9EG：274K LUT / 548K FF / 912 BRAM / 2520 DSP）

| 模块 | LUT | FF | BRAM | DSP | 占比 |
|------|-----|----|------|-----|------|
| DPU B4096 | 80K | 60K | 200 | 900 | 32% |
| 4× ISP HLS | 60K | 50K | 80 | 200 | 24% |
| 4× MIPI RX | 8K | 6K | 20 | 0 | 3% |
| VDMA × 2 | 5K | 4K | 16 | 0 | 2% |
| 10GbE MAC | 12K | 10K | 30 | 0 | 5% |
| OSD HLS | 10K | 8K | 10 | 20 | 4% |
| DisplayPort | 5K | 4K | 8 | 0 | 2% |
| AXI Infra | 8K | 6K | 0 | 0 | 3% |
| **合计** | **188K** | **148K** | **364** | **1120** | **~75%** |

保留 25% 余量用于时序收敛。

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | architect | 初始 |
