---
id: IF-REQ-001
title: MIPI CSI-2 4 lane 接收
type: requirement-interface
status: approved
owner: fpga-team
version: 1.0
traces: { up: [], down: [DES-ARCH-001, MOD-RTL-MIPI-RX] }
tags: [interface, video, mipi]
---

# IF-REQ-001: MIPI CSI-2 4 lane 接收

## 描述
4 路 MIPI CSI-2 4-lane D-PHY 接收，每路像素率 2.5 Gbps/lane。

## 规格
- 协议：MIPI CSI-2 v1.3
- 物理：D-PHY 1.2
- Lane 数：4（数据）+ 1（时钟）
- 速率：2.5 Gbps/lane
- 虚拟通道：0
- 数据类型：RAW10

## 验收准则
1. 4 lane 全部 ALIGNED 后才能采图
2. 物理层 ECC + CRC 校验开启
3. 支持 4K@30fps（~6 Gbps 像素率）

## 验证
- TC-IF-MIPI-001: 单 lane 拉偏测试
- TC-IF-MIPI-002: 4 lane 同步测试
