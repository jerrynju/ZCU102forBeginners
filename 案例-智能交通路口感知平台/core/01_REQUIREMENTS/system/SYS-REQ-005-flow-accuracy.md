---
id: SYS-REQ-005
title: 流量统计精度 > 95%
type: requirement-system
status: approved
owner: ai-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: [STK-REQ-001]
  down: [DES-ARCH-008, MOD-C-TRACK, MOD-C-EVENT, TC-FLOW-001]
tags: [system, statistics]
verification_method: integration_test
---

# SYS-REQ-005: 流量统计精度 > 95%

## 描述
在监控画面上由人工/工具标注虚拟线圈（直行、左转、右转），设备应能：
- 统计穿越线圈的车辆数（分车型：car/truck/bus/motorcycle）
- 估算车流平均速度（基于轨迹时间差与像素距离）
- 估算排队长度（车道上低速目标聚类）

## 验收准则
1. 流量计数误差 < 5%
2. 平均速度误差 < 10%
3. 排队长度误差 < 20%
4. 统计粒度：1 分钟
5. 上报延迟 < 60s

## 验证
- TC-FLOW-001: 自采视频 1h 视频对照人工计数
- TC-FLOW-002: 极端拥堵场景

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | zhao.qi | 初始 |
