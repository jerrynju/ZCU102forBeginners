---
id: TC-CAN-LATENCY
title: CAN 指令延迟测量
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-006]
  down: [TASK-SIG-FSM, TASK-CAN-RX]
tags: [test, real-time, can]
---

# TC-CAN-LATENCY: CAN 指令延迟测量

## 目的
测量从 A53 下发指令到 R5 通过 CAN 总线发送帧的端到端延迟。

## 入口
- 实机：[`06_INTEGRATION/ci-cd/run_can_latency.py`](../../06_INTEGRATION/ci-cd/run_can_latency.py)

## 步骤

1. 接入 CAN 总线分析仪（CANalyzer）
2. A53 发送 1000 次控制指令
3. R5 接收后通过 CAN 发送响应
4. 抓取每帧时间戳（A53 时间戳 + CAN 时间戳）
5. 统计分析

## 通过条件
- P95 延迟 < 10ms
- P99 延迟 < 20ms
- 帧丢失率 < 0.001%

## 失败处理
1. 延迟超标：检查 R5 中断优先级
2. 帧丢失：检查 CAN 总线负载
