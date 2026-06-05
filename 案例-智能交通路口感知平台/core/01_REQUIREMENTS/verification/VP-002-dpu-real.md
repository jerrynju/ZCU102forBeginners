---
id: VP-002
title: DPU 实机验证
type: verification-policy
status: approved
owner: qa-team
version: 1.0
traces: { up: [], down: [] }
tags: [verification, dpu, hardware]
---

# VP-002: DPU 实机验证

## 目标
在加载 FPGA 比特流后，验证 DPU 真实推理的精度与性能。

## 工具与位置
- 测试代码：`core/04_IMPLEMENTATION/ai/deploy/test_inference.py`
- 工厂测试：`core/06_INTEGRATION/ci-cd/factory_test.py`
- 报告：`core/05_VERIFICATION/reports/`

## 范围
1. 模型加载（xmodel）
2. 标准测试图片推理
3. 推理延迟 profiler
4. mAP benchmark（vs golden）
5. 24h 长稳测试

## 验收准则
1. YOLOv8s mAP50 ≥ 88%
2. LPRNet accuracy ≥ 95%
3. 单帧推理 ≤ 18ms

## 自动化
`sw-htf verify dpu` → release gate
