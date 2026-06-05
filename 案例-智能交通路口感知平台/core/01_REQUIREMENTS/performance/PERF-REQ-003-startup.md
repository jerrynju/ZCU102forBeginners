---
id: PERF-REQ-003
title: 启动时间 < 15s
type: requirement-performance
status: approved
owner: embedded-team
version: 1.0
traces: { up: [], down: [SYS-REQ-008] }
tags: [performance, startup]
verification_method: measurement
---

# PERF-REQ-003: 启动时间 < 15s

## 描述
从上电到 DPU 推理就绪的端到端启动时间 < 15s。

## 启动时间分配

| 阶段 | 预算 |
|------|------|
| BootROM → FSBL | 1s |
| PMU FW + ATF | 1s |
| U-Boot | 1s |
| Linux kernel | 2s |
| rootfs mount | 1s |
| systemd + 基础服务 | 2s |
| DPU 驱动加载 | 2s |
| xmodel 加载 | 1s |
| 应用启动 + 模型 warmup | 3s |
| **合计** | **~14s** |

## 验收准则
1. 上电 → 推理可用 < 15s
2. 重启 → 推理可用 < 10s

## 验证
- TC-PERF-BOOT-001: 100 次冷启动时间分布
