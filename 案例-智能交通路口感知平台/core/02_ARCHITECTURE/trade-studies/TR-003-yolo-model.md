---
id: TR-003
title: YOLO 模型选型（n/s/m）
type: trade-study
status: approved
owner: ai-team
version: 1.0
traces: { up: [SYS-REQ-002, SYS-REQ-004, PERF-REQ-004], down: [MOD-AI-YOLOV8S, MOD-AI-YOLOV8N] }
tags: [trade-study, ai, yolo]
---

# TR-003: YOLO 模型选型

## 候选（DPU B4096，INT8）

| 模型 | mAP50 | 推理耗时 | 模型大小 | 适用 |
|------|-------|---------|---------|------|
| YOLOv8n | 84.2% | 8ms | 3.2MB | 资源受限 |
| **YOLOv8s** | **88.5%** | **18ms** | **11MB** | **精度与速度平衡（推荐）** |
| YOLOv8m | 91.0% | 42ms | 26MB | 高精度场景 |

## 评估

| 维度 | 权重 | YOLOv8n | YOLOv8s | YOLOv8m |
|------|------|---------|---------|---------|
| 精度 | 0.4 | 3 | 4 | 5 |
| 速度 | 0.3 | 5 | 4 | 2 |
| 资源占用 | 0.2 | 5 | 3 | 1 |
| 训练成本 | 0.1 | 5 | 4 | 3 |
| **加权总分** | 1.0 | **4.0** | **3.9** | **3.0** |

## 决策

**主用：YOLOv8s**（精度+速度平衡）
**备选：YOLOv8n**（峰值拥堵时段降级使用）

详见代码中的自适应配置：
```python
config = {
    'daytime_normal':  {'model': 'yolov8s', 'conf': 0.4, 'nms': 0.5},
    'nighttime':       {'model': 'yolov8s', 'conf': 0.3, 'nms': 0.5},
    'peak_hour':       {'model': 'yolov8n', 'conf': 0.5, 'nms': 0.6},
}
```

## 验证
- TC-AI-DET-001: 精度 benchmark
- TC-AI-DET-004: 自适应切换测试
