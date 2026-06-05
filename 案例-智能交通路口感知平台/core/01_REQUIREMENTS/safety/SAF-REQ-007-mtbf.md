---
id: SAF-REQ-007
title: MTBF > 50,000 小时
type: requirement-safety
status: approved
owner: hw-team
version: 1.0
traces: { up: [STK-REQ-002], down: [] }
tags: [safety, reliability, mtbf]
verification_method: reliability_analysis
---

# SAF-REQ-007: MTBF > 50,000 小时

## 描述
平均故障间隔时间（MTBF）> 50,000 小时（≈ 5.7 年）。

## 措施
- 工业级器件选型
- eMMC 启用 wear-leveling + 健康监测
- DDR4 ECC
- 关键模块冗余（如双 SFP+）

## 验证
- TC-SAF-007: 加速寿命试验 + 现场数据回算
