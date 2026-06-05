---
id: SAF-REQ-003
title: 信号灯安全模式（全红）
type: requirement-safety
status: approved
owner: rtos-team
version: 1.0
traces: { up: [STK-REQ-002], down: [DES-ARCH-005, TASK-SIG-FSM] }
tags: [safety, signal-control, fault]
verification_method: fault_injection
---

# SAF-REQ-003: 信号灯安全模式（全红）

## 描述
当出现以下任一情况时，信号灯立即进入安全模式（全红 ALLRED）：
- A53 心跳超时
- CAN 控制器无响应
- 检测到异常相位状态
- 收到人工安全模式指令

## 验收准则
1. 任意故障触发后 100ms 内进入全红
2. 全红保持至少 5s
3. 故障恢复后 10s 内恢复自适应控制

## 验证
- TC-SAF-003: 故障注入测试
