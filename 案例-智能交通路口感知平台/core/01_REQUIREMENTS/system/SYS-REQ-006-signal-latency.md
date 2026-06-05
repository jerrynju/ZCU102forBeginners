---
id: SYS-REQ-006
title: 信号灯联动控制 < 10ms
type: requirement-system
status: approved
owner: rtos-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P1
traces:
  up: [STK-REQ-003]
  down: [DES-ARCH-005, DES-ARCH-006, IF-REQ-003, TASK-SIG-FSM, TASK-CAN-RX, TC-CAN-LATENCY]
tags: [system, real-time, signal-control]
verification_method: timing_analysis
---

# SYS-REQ-006: 信号灯联动控制 < 10ms

## 描述
R5 FreeRTOS 子系统接收到 A53 下发的控制指令后，应在 **< 10ms** 内通过 CAN 总线下发到信号灯控制器。

## 验收准则
1. A53 下发 → R5 接收 → R5 下发 CAN 帧：端到端 < 10ms
2. CAN 帧丢失率 < 0.001%
3. 信号灯控制器 ACK 接收率 100%
4. A53 故障时 R5 自动切换安全模式（ALLRED）

## 验证
- TC-CAN-LATENCY: 时间戳戳穿测量（中断到 CAN TX 完成）
- TC-CAN-DROP: 24h 持续帧率测试
- TC-FAIL-SAFE: A53 心跳停止后 5s 内 R5 切换安全模式

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | chen.ba | 初始 |
