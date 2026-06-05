---
id: SAF-REQ-006
title: 工作温度 -20°C ~ +70°C
type: requirement-safety
status: approved
owner: hw-team
version: 1.0
traces: { up: [STK-REQ-002], down: [DES-ARCH-001] }
tags: [safety, environment, thermal]
verification_method: chamber_test
---

# SAF-REQ-006: 工作温度 -20°C ~ +70°C

## 描述
设备应在工业级温度范围内稳定工作。

## 验收准则
1. -20°C 冷启动成功
2. +70°C 满负荷运行稳定
3. TJ < 95°C（结温上限）
4. 散热设计：自然散热 + 必要时主动风扇

## 验证
- TC-SAF-006: 高低温箱测试 24h
