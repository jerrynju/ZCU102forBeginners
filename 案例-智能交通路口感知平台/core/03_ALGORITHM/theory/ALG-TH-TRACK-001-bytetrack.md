---
id: ALG-TH-TRACK-001
title: ByteTrack 算法理论
type: algorithm-theory
status: approved
owner: ai-team
version: 1.0
traces:
  up: [DES-ARCH-008, SYS-REQ-004]
  down: [ALG-TRACK-001]
tags: [algorithm, tracking, theory]
---

# ALG-TH-TRACK-001: ByteTrack 算法理论

## 论文
Cao et al. "ByteTrack: Multi-Object Tracking by Associating Every Detection Box", ECCV 2022.

## 核心思想

传统 SORT 类方法只用高置信度检测（score > 0.5）做关联，丢弃低分检测。但低分检测往往来自
**遮挡或运动模糊**的目标，丢弃它们会导致 ID 切换。

**ByteTrack 创新**：将所有低分检测也用于二次关联。

## 流程

```
高置信度检测 (score > 0.5)  +  上一帧轨迹
        ↓ IoU 匹配
        ↓ 第一关联
   未匹配轨迹
        ↓
低置信度检测 (0.1 < score < 0.5)  +  未匹配轨迹
        ↓ IoU 匹配（更宽松）
        ↓ 第二关联
   最终未匹配轨迹 → 删除（连续 N 帧未匹配）
   最终未匹配检测 → 初始化新轨迹
```

## 卡尔曼运动模型

```
状态: x = [cx, cy, s, r, vx, vy, vs]
cx, cy: 中心坐标
s: 面积（bbox 像素数）
r: 宽高比
v*: 速度
```

匀速运动 + 线性观测。

## IoU 匹配

匹配代价 = 1 - IoU(prev_bbox, curr_bbox)
使用匈牙利算法求解最优分配。

## 实现要点

1. **Score 阈值**：0.5 / 0.1 是经验值，可调
2. **连续丢失帧容忍**：max_time_lost = 30 帧
3. **新轨迹 min_hits**：连续 3 帧匹配才输出（防抖）

## 实现位置

- Python 仿真：[03_ALGORITHM/simulation/src/bytetrack_simple.py](../../03_ALGORITHM/simulation/src/bytetrack_simple.py)
- C++ 实现：[04_IMPLEMENTATION/c/src/app/byte_tracker.cpp](../../04_IMPLEMENTATION/c/src/app/byte_tracker.cpp)

## 验证

- TC-TRACK-001: MOT17 MOTA ≥ 75%
