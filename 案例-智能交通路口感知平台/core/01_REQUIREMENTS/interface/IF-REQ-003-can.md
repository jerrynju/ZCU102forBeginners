---
id: IF-REQ-003
title: CAN 2.0B 总线
type: requirement-interface
status: approved
owner: rtos-team
version: 1.0
traces: { up: [], down: [DES-ARCH-005, TASK-CAN-RX] }
tags: [interface, can, signal-control]
---

# IF-REQ-003: CAN 2.0B 总线

## 描述
1 路 CAN 2.0B 总线，连接信号灯控制器与地感线圈。

## 规格
- 协议：CAN 2.0B（11-bit 标准帧 + 29-bit 扩展帧）
- 速率：500 Kbps
- PHY：SN65HVD230
- 控制器：Xilinx AXI CAN 2.0B

## 帧 ID 分配

| ID | 方向 | 用途 |
|----|------|------|
| 0x101 | → | 信号灯控制命令 |
| 0x102 | ← | 信号灯状态反馈 |
| 0x200 | ← | 地感线圈计数 |
| 0x7FF | → | 心跳 |

## 验收准则
1. 帧丢失率 < 0.001%
2. 端到端延迟 < 1ms
3. 总线关闭自动恢复

## 验证
- TC-IF-CAN-001: 24h 帧率测试
- TC-IF-CAN-002: 总线故障恢复
