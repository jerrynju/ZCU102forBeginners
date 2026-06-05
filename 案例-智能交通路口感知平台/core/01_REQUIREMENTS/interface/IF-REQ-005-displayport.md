---
id: IF-REQ-005
title: DisplayPort 1.2 输出
type: requirement-interface
status: approved
owner: fpga-team
version: 1.0
traces: { up: [], down: [DES-ARCH-001, MOD-HLS-OSD] }
tags: [interface, display, video]
---

# IF-REQ-005: DisplayPort 1.2 输出

## 描述
1 路 DisplayPort 1.2 输出，连接本地运维显示器，输出 4K 合成画面。

## 规格
- 协议：DisplayPort 1.2
- 分辨率：3840×2160@30fps
- 多流：2 流（监控 + 检测框叠加）

## 验收准则
1. 4K 实时合成
2. 检测框叠加延迟 < 50ms

## 验证
- TC-IF-DP-001: 4K 链路训练
- TC-IF-DP-002: 检测框叠加测试
