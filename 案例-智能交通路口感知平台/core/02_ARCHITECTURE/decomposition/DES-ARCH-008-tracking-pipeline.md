---
id: DES-ARCH-008
title: 多目标跟踪管线
type: design-architecture
status: approved
owner: ai-team
version: 1.0
traces: { up: [SYS-REQ-002, SYS-REQ-003, SYS-REQ-004, SYS-REQ-005], down: [MOD-C-TRACK, MOD-C-EVENT, ALG-TRACK-001] }
tags: [architecture, tracking, bytetrack]
---

# DES-ARCH-008: 多目标跟踪管线

## 流程

```
DPU YOLO 检测
  ↓
ByteTrack 两阶段关联
  ├── 第一关联：高分检测 (score > 0.5)
  └── 第二关联：低分检测 (0.1 < score < 0.5)
  ↓
卡尔曼滤波运动模型
  ↓
输出 track_id + bbox + class
  ↓
事件检测（虚拟线圈/方向判断/停车线检测）
```

## 算法要点

- **ByteTrack**：将所有低分检测也用于关联，提升遮挡目标找回率
- **卡尔曼滤波**：匀速运动模型
- **匹配代价**：IoU + 距离加权
- **ID 切换保护**：track_id ≥ 1 的目标进入"锁定"状态（连续 3 帧匹配不丢失）

## 性能

- 单帧跟踪 < 2ms（64 目标上限）
- MOTA > 75%（MOT17）
- IDF1 > 70%

## 接口

```cpp
// 输入
struct Detection { uint8_t class_id; float score; BBox bbox; };

// 输出
struct Track { int32_t track_id; BBox bbox; uint8_t class_id; int age; };
```

## 验证
- TC-TRACK-001: MOT17 公开数据集
- TC-TRACK-002: 自采数据长轨迹
