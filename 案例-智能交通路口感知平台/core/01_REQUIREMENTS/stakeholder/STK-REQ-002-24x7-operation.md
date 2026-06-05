---
id: STK-REQ-002
title: 24 小时无人值守运行
type: requirement-stakeholder
status: approved
owner: customer-success
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: []
  down: [SAF-REQ-001, SAF-REQ-002, SYS-REQ-009, SYS-REQ-010, SYS-REQ-008]
tags: [stakeholder, reliability, sla]
---

# STK-REQ-002: 24 小时无人值守运行

## 描述
设备安装后应能在无人现场维护的情况下 **7×24** 持续运行：
- 故障应能 **自动恢复**（如软件 watchdog 重启）
- 升级应能 **远程完成**（OTA），不需要现场操作
- 异常应能 **主动上报**（云端告警 + 日志）

## 验收准则
1. MTBF > 50,000 小时
2. 现场维护频率 < 1 次/年
3. 关键故障 5 分钟内主动上报云端
4. 离线工作 ≥ 24 小时

## 干系人
- 决策：交通局采购科
- 验收：交通局运维科
- 使用：现场无人值守
