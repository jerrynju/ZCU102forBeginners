---
id: TC-FLOW-001
title: 流量统计精度
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-005]
  down: [MOD-C-TRACK, MOD-C-EVENT]
tags: [test, flow-statistics]
---

# TC-FLOW-001: 流量统计精度

## 目的
验证设备在自采视频上的流量统计精度。

## 入口
- 仿真：[`03_ALGORITHM/simulation/src/traffic_sim.py`](../../03_ALGORITHM/simulation/src/traffic_sim.py) --mode flow
- 实机：[`06_INTEGRATION/ci-cd/run_flow_test.py`](../../06_INTEGRATION/ci-cd/run_flow_test.py)

## 步骤

1. 在 1h 自采视频上标定虚拟线圈
2. 设备统计 1h 流量
3. 人工标定 ground truth
4. 计算误差

## 通过条件

| 指标 | 最低 |
|------|------|
| 流量计数误差 | < 5% |
| 平均速度误差 | < 10% |
| 排队长度误差 | < 20% |

## 失败处理
1. 漏检：调低置信度阈值
2. 误检：提高置信度 / NMS
3. 速度误差大：标定像素当量
