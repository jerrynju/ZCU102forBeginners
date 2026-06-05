---
id: TC-CLOUD-001
title: 云端事件上报延迟分布
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-007]
  down: [MOD-C-CLOUD, MOD-C-OFFLINE]
tags: [test, cloud, latency]
---

# TC-CLOUD-001: 云端事件上报延迟分布

## 目的
验证 1000 次事件上报到云端 ACK 的延迟分布。

## 入口
- 仿真：[`03_ALGORITHM/simulation/src/traffic_sim.py`](../../03_ALGORITHM/simulation/src/traffic_sim.py) --mqtt localhost --frames 1000
- 实机：[`06_INTEGRATION/ci-cd/run_cloud_test.py`](../../06_INTEGRATION/ci-cd/run_cloud_test.py)

## 步骤

1. 配置本地 EMQX + 业务 ACK 服务
2. 仿真生成 1000 个违章事件
3. 设备上报
4. ACK 时间戳记录
5. 统计分析

## 通过条件
- P95 延迟 < 500ms
- P99 延迟 < 1s
- 100% ACK 收到

## 失败处理
1. 网络抖动：开启 QoS 1 + 重传
2. 业务 ACK 慢：优化业务服务
3. 本地 MQTT 慢：调 QoS、限速
