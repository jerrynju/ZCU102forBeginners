---
id: TC-TRACK-001
title: ByteTrack MOTA benchmark
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-004]
  down: [MOD-C-TRACK, ALG-TRACK-001]
tags: [test, tracking, benchmark]
---

# TC-TRACK-001: ByteTrack MOTA benchmark

## 目的
验证 ByteTrack 在 MOT17 数据集上的多目标跟踪精度。

## 入口
- 仿真：[`03_ALGORITHM/simulation/src/bytetrack_simple.py`](../../03_ALGORITHM/simulation/src/bytetrack_simple.py) --bench

## 数据集
- MOT17 train（7 序列，5466 帧）

## 指标
- MOTA
- IDF1
- ID Switches (IDS)
- Fragmentation (Frag)

## 通过条件

| 指标 | 最低 |
|------|------|
| MOTA | 75% |
| IDF1 | 70% |
| IDS | < 200 |

## 失败处理
1. 检测器精度低：先用更高精度检测器
2. 遮挡目标丢失：调整 ByteTrack 低分阈值
3. 速度估计漂移：调卡尔曼 Q
