---
id: ICD-005
title: CAN 总线帧定义
type: interface-control
status: approved
owner: rtos-team
version: 1.0
traces: { up: [IF-REQ-003, DES-ARCH-005], down: [TASK-CAN-RX] }
tags: [interface, can]
---

# ICD-005: CAN 总线帧定义

## 物理层

- 协议：CAN 2.0B
- 速率：500 Kbps
- 帧类型：标准帧（11-bit ID）
- PHY：SN65HVD230

## 帧 ID 分配

| ID | 方向 | 名称 | DLC |
|----|------|------|-----|
| 0x101 | → 控制器 | 信号灯控制命令 | 2 |
| 0x102 | ← 控制器 | 信号灯状态反馈 | 4 |
| 0x200 | ← 线圈 | 地感线圈计数 | 1 |
| 0x7FF | → 总线 | 心跳 | 0 |

## 0x101 信号灯控制命令

| Byte 0 | Byte 1 |
|--------|--------|
| phase (4bit) + checksum (4bit) | duration_high (8bit) |

- phase：SignalPhase_t（参见 DES-ARCH-005）
- checksum：低 4 位 XOR 校验

## 0x102 信号灯状态反馈

| Byte 0 | Byte 1 | Byte 2 | Byte 3 |
|--------|--------|--------|--------|
| current_phase | timer_remaining_s | alarm_flags | checksum |

- alarm_flags：bit0=通信故障, bit1=灯具故障

## 0x200 地感线圈计数

| Byte 0 |
|--------|
| bit0-3: 4 个线圈方向，1=有车 |

## 验证
- TC-IF-CAN-001: 24h 帧率测试
- TC-IF-CAN-002: 总线故障恢复
