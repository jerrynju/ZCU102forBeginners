---
id: TC-OFFLINE-24H
title: 离线 24h 工作
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-010]
  down: [MOD-C-OFFLINE]
tags: [test, offline, endurance]
---

# TC-OFFLINE-24H: 离线 24h 工作

## 目的
验证设备在网络断连 24h 后仍能正常工作并补传数据。

## 步骤

1. 启动仿真/实机业务
2. 拔除网络（拔 10GbE 光纤 + 关 4G）
3. 持续 24h
4. 期间触发 1000 个事件
5. 重新接入网络
6. 观察补传

## 通过条件
- 24h 业务功能 100% 正常
- 缓存数据 100% 上传
- 补传 < 1h
- 重连不丢数据

## 失败处理
1. 缓存满：调整滚动策略
2. 补传慢：提升限速
3. 业务中断：检查 SQLite 锁
