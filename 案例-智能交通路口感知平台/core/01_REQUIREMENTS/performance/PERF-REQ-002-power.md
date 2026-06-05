---
id: PERF-REQ-002
title: 整机功耗 < 35W
type: requirement-performance
status: approved
owner: hw-team
version: 1.0
traces: { up: [], down: [DES-ARCH-001] }
tags: [performance, power]
verification_method: measurement
---

# PERF-REQ-002: 整机功耗 < 35W

## 描述
设备整机功耗（含 MPSoC + DDR4 + 4×ISP + 10GbE MAC + OSD）< 35W（不含 4 路摄像头 PoE 供电）。

## 功耗分配估算

| 模块 | 功耗 |
|------|------|
| MPSoC PS (A53+R5) | 5W |
| MPSoC PL (DPU+ISP+OSD+MAC) | 18W |
| DDR4 4GB | 4W |
| 10GbE MAC + PHY | 3W |
| DisplayPort | 1.5W |
| CAN, GPIO, 其他 | 1.5W |
| **合计** | **33W** |

## 验收准则
1. 满负荷推理 < 35W
2. 待机 < 25W

## 验证
- TC-PERF-PWR-001: 功耗计测试
