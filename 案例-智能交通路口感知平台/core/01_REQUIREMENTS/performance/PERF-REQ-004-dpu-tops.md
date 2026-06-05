---
id: PERF-REQ-004
title: DPU ≥ 2.5 TOPS
type: requirement-performance
status: approved
owner: ai-team
version: 1.0
traces: { up: [], down: [DES-ARCH-001, TR-003] }
tags: [performance, ai, dpu]
verification_method: benchmark
---

# PERF-REQ-004: DPU ≥ 2.5 TOPS

## 描述
DPU B4096 实际峰值算力 ≥ 2.5 TOPS（INT8）。

## 计算
- DPU B4096：4096 × 300 MHz × 2 ops = 2,457,600,000 ops = 2.46 TOPS
- 实测因数据复用：~2.0 TOPS

## 验收准则
1. vaitrace profiler 显示 ≥ 2.0 TOPS
2. YOLOv8s 端到端 ≥ 40 FPS（含前后处理）

## 验证
- TC-PERF-DPU-001: vai profiler benchmark
