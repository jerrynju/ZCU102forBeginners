---
id: SYS-REQ-002
title: 车辆/行人检测 mAP50 > 85%
type: requirement-system
status: verified
owner: ai-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: [STK-REQ-001]
  down: [DES-ARCH-008, TR-003, MOD-AI-YOLOV8S, MOD-C-INFER, TC-AI-DET-001]
tags: [system, ai, detection]
verification_method: benchmark
---

# SYS-REQ-002: 车辆/行人检测 mAP50 > 85%

## 描述
对 1080p 输入图像，设备应能识别以下 6 类目标并输出类别、置信度、bbox：
- car, truck, bus, person, motorcycle, bicycle

## 验收准则
1. 总体 mAP50 ≥ 85%（VisDrone/UA-DETRAC 验证集）
2. 单类 mAP50 ≥ 80%
3. 单帧推理延迟 < 30ms（4 路并行）
4. 最小可检测目标：32×32 像素

## 数据集
- 训练：VisDrone + UA-DETRAC + 自采 100h 路口
- 验证：自采路口数据 5000 张
- 测试：CCPD-BDD + 极端场景

## 模型
- YOLOv8s INT8（vitis-ai 编译）
- 输入：640×640
- 输出：6 类检测框

## 验证
- TC-AI-DET-001: 公开数据集精度 benchmark
- TC-AI-DET-002: 自采路口数据精度测试
- TC-AI-DET-003: 极端场景鲁棒性（夜晚/雨天/逆光）

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | wang.wu | 初始 |
