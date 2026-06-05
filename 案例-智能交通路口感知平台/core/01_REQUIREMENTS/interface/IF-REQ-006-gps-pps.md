---
id: IF-REQ-006
title: GPS PPS 时间同步
type: requirement-interface
status: approved
owner: rtos-team
version: 1.0
traces: { up: [], down: [DES-ARCH-005, TASK-PPS-SYNC] }
tags: [interface, time, gps]
---

# IF-REQ-006: GPS PPS 时间同步

## 描述
GPS 接收机每秒输出一个 PPS 脉冲，接入 PL GPIO，触发 R5 中断，用于跨摄像头帧时间戳对齐。

## 规格
- 信号：1 PPS TTL 脉冲
- 上升沿触发
- 抖动 < 100ns

## 验收准则
1. 时间戳同步误差 < 1ms
2. 4 路摄像头帧时间戳可对齐

## 验证
- TC-IF-PPS-001: PPS 抖动测试
- TC-IF-PPS-002: 帧时间戳一致性
