---
id: ADR-002
title: 信号灯控制部署到 R5 FreeRTOS
type: adr
status: accepted
owner: architect-team
version: 1.0
created: 2026-06-04
traces: { up: [], down: [DES-ARCH-005, SYS-REQ-006] }
tags: [decision, rtos, signal-control]
---

# ADR-002: 信号灯控制部署到 R5 FreeRTOS

## 状态
已接受（2026-06-04）

## 背景
信号灯控制指令端到端延迟要求 < 10ms。候选部署位置：
- A53 Linux（与 AI 推理同侧）
- R5 FreeRTOS（独立硬实时核）
- 外部 MCU（独立 ST/STM32）

## 决策
**采用 R5 FreeRTOS**

## 理由
1. **实时性**：FreeRTOS 无 Linux 调度抖动，10ms 周期硬保证
2. **集成度**：MPSOC 内置 R5，无需外部 MCU（成本、可靠性）
3. **故障隔离**：A53 故障时 R5 仍可工作（信号灯切安全模式）
4. **通信**：OpenAMP RPMsg 内置，与 A53 高速核间通信

## 取舍
- 代价：需要维护 R5 firmware（额外开发、编译、烧录）
- 替代方案：Linux + SCHED_FIFO（无法保证硬实时）

## 后果
- 需要 OpenAMP 框架（Xilinx 提供）
- 共享内存 256MB（DRE 区域）
- 心跳 + 看门狗（A53 故障时 R5 接管）

## 验证
- TC-CAN-LATENCY: 1000 次指令延迟
- TC-SAF-002: A53 故障时 R5 切换安全模式

## 关联
- 受影响需求：SYS-REQ-006, SAF-REQ-002, SAF-REQ-003
- 受影响设计：DES-ARCH-005, DES-ARCH-006
- 受影响任务：TASK-SIG-FSM, TASK-WATCHDOG, TASK-OPENAMP
