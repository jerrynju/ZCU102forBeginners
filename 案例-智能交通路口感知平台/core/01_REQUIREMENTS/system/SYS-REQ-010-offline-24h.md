---
id: SYS-REQ-010
title: 离线工作 24h
type: requirement-system
status: approved
owner: backend-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P1
traces:
  up: [STK-REQ-002]
  down: [DES-ARCH-010, MOD-C-OFFLINE, TC-OFFLINE-24H]
tags: [system, offline, reliability]
verification_method: endurance_test
---

# SYS-REQ-010: 离线工作 24h

## 描述
云端断连后设备仍能：
- 继续本地业务（检测、跟踪、事件检测）
- 将待上报数据持久化到本地 SQLite
- 24h 重连后自动补传所有数据

## 验收准则
1. 离线 24h 期间业务功能不中断
2. 离线期间累计数据量 < 4GB（8MB/h）
3. 重连后 1h 内完成补传
4. 补传过程限速 1MB/s

## 验证
- TC-OFFLINE-24H: 24h 持续运行 + 补传
- TC-OFFLINE-CAPACITY: 满负荷 4GB 补传

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | li.si | 初始 |
