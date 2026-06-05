---
id: PERF-REQ-005
title: DDR4 实际带宽 ≥ 30 GB/s
type: requirement-performance
status: approved
owner: fpga-team
version: 1.0
traces: { up: [], down: [DES-ARCH-002, DES-ARCH-003] }
tags: [performance, ddr, bandwidth]
verification_method: benchmark
---

# PERF-REQ-005: DDR4 实际带宽 ≥ 30 GB/s

## 描述
DDR4-2400 64-bit 理论带宽 38.4 GB/s，实测利用率 ≥ 78%。

## 利用率分配

| 端口 | 用途 | 峰值 |
|------|------|------|
| HP0 | VDMA 写（摄像头→DDR） | 6 GB/s |
| HP1 | DPU 读（DDR→DPU） | 3 GB/s |
| HP2 | DPU 写（DDR 输出） | 1 GB/s |
| HP3 | OSD 读（DDR→显示） | 1 GB/s |
| HPC0 | A53 网络 DMA | 1 GB/s |
| HPC1 | A53 应用 | 1 GB/s |
| **总计** | | **~13 GB/s（占 34%）** |

裕量充足，DPU 峰值 2.5 TOPS 折算 DDR 带宽约 20 GB/s，未到瓶颈。

## 验收准则
1. AXI Performance Monitor 显示 ≥ 30 GB/s 实际吞吐（理论上限测试）

## 验证
- TC-PERF-DDR-001: AXI PM 长时间监测
