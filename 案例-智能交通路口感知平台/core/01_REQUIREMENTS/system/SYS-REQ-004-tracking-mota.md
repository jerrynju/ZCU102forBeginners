---
id: SYS-REQ-004
title: 多目标跟踪 MOTA > 75%
type: requirement-system
status: verified
owner: ai-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: [STK-REQ-001]
  down: [DES-ARCH-008, MOD-C-TRACK, ALG-TRACK-001, TC-TRACK-001]
tags: [system, ai, tracking]
verification_method: benchmark
---

# SYS-REQ-004: 多目标跟踪 MOTA > 75%

## 描述
对检测输出进行跨帧关联，为每个目标分配稳定 track_id，用于：
- 流量统计（虚拟线圈穿越）
- 违章事件（轨迹方向判断）
- 车牌识别结果绑定（同一车辆多次出现的车牌合并）

## 验收准则
1. MOTA ≥ 75%（MOT16/MOT17 验证集）
2. IDF1 ≥ 70%
3. 单帧跟踪延迟 < 2ms
4. 最大同时跟踪目标数：64

## 算法
- ByteTrack（两阶段关联：高/低分检测）
- 卡尔曼滤波运动模型
- IoU + 距离匹配

## 验证
- TC-TRACK-001: MOT17 公开数据集
- TC-TRACK-002: 自采数据长轨迹测试
- TC-TRACK-003: 拥挤场景 ID 切换率

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | wang.wu | 初始 |
