---
id: STK-REQ-004
title: 数据上报云平台做大数据分析
type: requirement-stakeholder
status: approved
owner: data-platform
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: []
  down: [SYS-REQ-007, ICD-003, SAF-REQ-004]
tags: [stakeholder, cloud, data]
---

# STK-REQ-004: 数据上报云平台做大数据分析

## 描述
EdgeVision-T1 部署后应将以下数据上报城市云平台：
- **流量统计**（每分钟）：各方向车流量、平均速度、排队长度、占有率
- **违章事件**（实时触发）：违章类型、车牌、时间、图片证据
- **设备状态**（每 10s）：CPU/内存/温度/DPU 利用率

数据上报应 **加密**（TLS）、**有序**（QoS 1）、**可重传**（离线缓存）。

## 验收准则
1. 单设备日均上报数据 < 100MB
2. 流量统计延迟 < 60s
3. 违章事件延迟 < 1s
4. 离线 24h 后重连能补传所有数据
5. 通过 mTLS 双向认证

## 干系人
- 决策：交通局大数据中心
- 验收：云平台运维
- 使用：城市交通数据分析师
