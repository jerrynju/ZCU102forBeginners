---
id: IF-REQ-002
title: 10GbE SFP+ 光口
type: requirement-interface
status: approved
owner: fpga-team
version: 1.0
traces: { up: [], down: [DES-ARCH-001, MOD-RTL-XXV-ETH] }
tags: [interface, network, 10gbe]
---

# IF-REQ-002: 10GbE SFP+ 光口

## 描述
1 路 10GbE SFP+ 光纤接口，连接城市云平台。

## 规格
- 协议：10GBASE-R
- PHY：SFP+ 光模块
- MAC：Xilinx XXV Ethernet IP
- 数据通道：GTH Bank 226 Lane 0/1
- 参考时钟：156.25 MHz

## 验收准则
1. 线速 10 Gbps 转发
2. 支持 64B-9000B 帧长
3. PTP 时间同步（可选）

## 验证
- TC-IF-10G-001: iperf3 9 Gbps
- TC-IF-10G-002: 长帧 9000B 测试
