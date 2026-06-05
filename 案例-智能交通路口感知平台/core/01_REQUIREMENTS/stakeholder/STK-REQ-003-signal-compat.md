---
id: STK-REQ-003
title: 与现有信号灯系统兼容
type: requirement-stakeholder
status: approved
owner: integration
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: []
  down: [IF-REQ-003, SYS-REQ-006, DES-ARCH-005]
tags: [stakeholder, integration, signal-control]
---

# STK-REQ-003: 与现有信号灯系统兼容

## 描述
EdgeVision-T1 部署后应能：
- **读取** 现有信号灯控制器状态（绿灯/红灯/黄灯）
- **下发** 自适应配时建议（推荐相位时长）
- **不替换** 现有信号灯控制器（仅作为智能外设挂接）

## 验收准则
1. 支持主流信号灯控制器协议（SCATS / SCOOT / NTCIP / CAN 私有协议）
2. 单向控制指令响应时间 < 10ms
3. 与 A/B 厂家控制器完成现场联调

## 干系人
- 决策：交通局信控科
- 验收：信控工程师
- 使用：信控运维
