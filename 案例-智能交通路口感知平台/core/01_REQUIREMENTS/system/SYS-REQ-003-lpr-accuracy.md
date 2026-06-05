---
id: SYS-REQ-003
title: 车牌识别准确率 > 95%
type: requirement-system
status: verified
owner: ai-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: [STK-REQ-001]
  down: [DES-ARCH-008, MOD-AI-LPRNET, TC-AI-LPR-001]
tags: [system, ai, lpr]
verification_method: benchmark
---

# SYS-REQ-003: 车牌识别准确率 > 95%

## 描述
对检测到的车辆，在 ROI（车牌区域）裁剪后送入 LPRNet，输出车牌号（含省份简称）。

## 验收准则
1. 单字符识别准确率 ≥ 99%
2. 整牌识别准确率 ≥ 95%（CCPD-2019 验证集）
3. 单张车牌推理 < 50ms
4. 支持：单行车牌、新能源车牌、警用车牌、使领馆车牌
5. 支持省份简称：京/津/沪/渝/冀/豫/云/辽/黑/湘/皖/鲁/新/苏/浙/赣/鄂/桂/甘/晋/蒙/陕/吉/闽/贵/粤/川/青/藏/琼/宁

## 模型
- LPRNet INT8
- 输入：96×24 RGB
- 输出：CTC 序列（最多 8 字符 + blank）

## 验证
- TC-AI-LPR-001: CCPD-2019 整牌准确率
- TC-AI-LPR-002: 倾斜车牌鲁棒性
- TC-AI-LPR-003: 夜间车牌识别

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | wang.wu | 初始 |
