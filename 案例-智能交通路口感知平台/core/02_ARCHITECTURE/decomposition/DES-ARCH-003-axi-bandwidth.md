---
id: DES-ARCH-003
title: 总线带宽规划
type: design-architecture
status: approved
owner: architect-team
version: 1.0
traces: { up: [PERF-REQ-005], down: [] }
tags: [architecture, axi, bandwidth]
---

# DES-ARCH-003: 总线带宽规划

## AXI 端口分配

| 端口 | 方向 | 用途 | 峰值 |
|------|------|------|------|
| HP0 | PL→DDR | 视频 DMA 写入（摄像头→DDR） | ~6 GB/s |
| HP1 | DDR→PL | DPU 输入读取（DDR→DPU） | ~3 GB/s |
| HP2 | PL→DDR | DPU 输出写入 | ~1 GB/s |
| HP3 | DDR→PL | OSD/Display 读取 | ~1 GB/s |
| HPC0 | A53↔DDR | Linux DMA（网络收发） | ~1 GB/s |
| HPC1 | A53↔DDR | A53 应用内存访问 | ~1 GB/s |

**总理论带宽**：DDR4-2400 × 64bit = 38.4 GB/s（实测利用率 ~60%，仍有大量余量）

## 关键设计

1. **HP 端口隔离**：4 个 HP 端口分别绑定不同业务，避免总线争用
2. **QoS 优先级**：视频流 QoS=3 > DPU QoS=2 > A53 QoS=0
3. **突发传输**：所有 DMA 配置为 4KB 突发，最小化 AXI 事务数

## 验证
- TC-PERF-DDR-001: AXI Performance Monitor 长稳测试
