---
id: TC-AI-DET-001
title: YOLOv8s 检测精度 benchmark
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-002]
  down: [MOD-AI-YOLOV8S, MOD-C-INFER]
tags: [test, ai, detection, benchmark]
---

# TC-AI-DET-001: YOLOv8s 检测精度 benchmark

## 目的
在公开数据集上验证 YOLOv8s INT8 模型精度退化在可接受范围内。

## 入口
- 仿真：[`04_IMPLEMENTATION/ai/deploy/test_inference.py`](../../04_IMPLEMENTATION/ai/deploy/test_inference.py) --benchmark
- 评估：[`04_IMPLEMENTATION/ai/quantization/ptq_quantize.py`](../../04_IMPLEMENTATION/ai/quantization/ptq_quantize.py) --eval

## 数据集
- VisDrone 2019 DET val (548 视频片段)
- UA-DETRAC test (60 视频)
- 自采 5000 张路口数据

## 步骤

1. 加载 `yolov8s_traffic_int8.xmodel`
2. 对测试集做推理
3. mAP50 计算（pycocotools）
4. 类别级精度分析

## 通过条件

| 类别 | mAP50 最低 |
|------|-----------|
| car | 90% |
| truck | 85% |
| bus | 88% |
| person | 80% |
| motorcycle | 75% |
| bicycle | 70% |
| **总体** | **85%** |

## 失败处理
1. 量化掉点：扩大 calib 集 / 改用 QAT
2. 类别不平衡：增加数据
3. 小目标掉点：提高输入分辨率
