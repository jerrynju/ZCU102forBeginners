---
id: SAF-REQ-002
title: A53→R5 看门狗心跳
type: requirement-safety
status: approved
owner: rtos-team
version: 1.0
traces: { up: [STK-REQ-002], down: [DES-ARCH-005, DES-ARCH-006] }
tags: [safety, watchdog, real-time]
verification_method: fault_injection
---

# SAF-REQ-002: A53→R5 看门狗心跳

## 描述
A53 每秒向 R5 发送心跳；R5 在 5s 内未收到心跳视为 A53 故障。

## 处理策略
A53 故障时 R5 立即：
1. 切换信号灯到安全模式（ALLRED）
2. 持续尝试通知 A53（若已恢复）
3. 上报告警到云端（若网络可用）

## 验收准则
1. 心跳丢失检测时间 < 5s
2. 切换 ALLRED 时间 < 100ms
3. A53 恢复后 10s 内 R5 退出安全模式

## 验证
- TC-SAF-002: kill -9 A53 推理进程 → R5 切换 ALLRED
