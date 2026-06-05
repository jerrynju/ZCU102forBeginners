---
id: TC-AI-LPR-001
title: LPRNet 车牌识别精度 benchmark
type: test-case
status: approved
owner: qa-team
version: 1.0
traces:
  up: [SYS-REQ-003]
  down: [MOD-AI-LPRNET, MOD-C-INFER]
tags: [test, ai, lpr, benchmark]
---

# TC-AI-LPR-001: LPRNet 车牌识别精度 benchmark

## 目的
验证 LPRNet INT8 在 CCPD 验证集上的整牌识别准确率。

## 入口
- 仿真：[`04_IMPLEMENTATION/ai/deploy/test_inference.py`](../../04_IMPLEMENTATION/ai/deploy/test_inference.py) --test lpr

## 数据集
- CCPD 2019 val（5000 张）

## 步骤

1. 加载 `lprnet_int8.xmodel`
2. 对测试集做推理
3. 计算整牌准确率
4. 字符级准确率（substring）
5. 单字符准确率

## 通过条件

| 指标 | 最低 |
|------|------|
| 整牌准确率 | 95% |
| 7 字符匹配 | 97% |
| 单字符 | 99% |
| 推理延迟 | < 50ms |

## 失败处理
1. 倾斜车牌差：增加仿射变换增强
2. 新能源车牌差：单独收集数据
3. 夜间车牌差：增加低光照数据
