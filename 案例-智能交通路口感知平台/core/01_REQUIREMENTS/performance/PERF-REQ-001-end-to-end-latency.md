---
id: PERF-REQ-001
title: 端到端检测延迟 < 30ms/帧
type: requirement-performance
status: approved
owner: fpga-team
version: 1.0
traces: { up: [], down: [DES-ARCH-001, DES-ARCH-007, DES-ARCH-008] }
tags: [performance, latency]
verification_method: timing_analysis
---

# PERF-REQ-001: 端到端检测延迟 < 30ms/帧

## 描述
从摄像头感光到 4 路全帧检测结果输出的 P95 端到端延迟 < 30ms。

## 延迟预算分配

| 阶段 | 预算 | 实测 |
|------|------|------|
| 摄像头曝光 | 8ms | 8ms |
| MIPI 接收 + ISP | 5ms | 4ms |
| DDR 写入 | 1ms | 1ms |
| DPU 推理（轮询 4 路） | 8ms × 4 = 32ms | 22ms（含 4 路轮询）|
| 后处理 (NMS + 跟踪) | 2ms | 1ms |
| **单帧平均** | **~12ms** | **8.5ms** |
| **4 路总吞吐** | **≥ 30fps** | **~40fps** |

## 验收准则
1. 单帧 P95 延迟 < 30ms
2. 4 路 P95 延迟 < 30ms/帧

## 验证
- TC-PERF-LAT-001: 1h 延迟分布测试
