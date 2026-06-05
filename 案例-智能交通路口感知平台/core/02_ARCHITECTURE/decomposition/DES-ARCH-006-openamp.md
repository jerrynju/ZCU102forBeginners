---
id: DES-ARCH-006
title: OpenAMP 通信协议
type: design-architecture
status: approved
owner: rtos-team
version: 1.0
traces: { up: [SYS-REQ-006, SAF-REQ-002], down: [TASK-OPENAMP] }
tags: [architecture, openamp, rpmsg]
---

# DES-ARCH-006: OpenAMP 通信协议（A53 ↔ R5）

## 端点

- Endpoint: `traffic-ctrl`
- Address: 0x400

## 消息类型

| Type | 方向 | 用途 |
|------|------|------|
| MSG_TYPE_CTRL_CMD | A53→R5 | 控制指令（相位/时长/手动接管）|
| MSG_TYPE_PHASE_QUERY | A53→R5 | 查询当前相位 |
| MSG_TYPE_STATUS_RESP | R5→A53 | 状态响应 |
| MSG_TYPE_COUNT_REPORT | R5→A53 | 车辆计数上报 |
| MSG_TYPE_HEARTBEAT | 双向 | 心跳（1Hz） |

## 帧结构

```c
typedef struct __attribute__((packed)) {
    uint8_t  type;          // 消息类型
    uint8_t  seq;           // 序列号
    uint16_t length;        // payload 长度
    uint8_t  payload[60];   // 实际数据
} RPMsgFrame_t;
```

## 性能指标

- 端到端延迟（A53 用户态→R5 任务）< 1ms
- 带宽 ≥ 100 msg/s
- 心跳超时 5s

## 共享内存

- DDR4 0xB8000000 - 0xBFFFFFFF（256MB，ECC 保护）
- 仅用于大块数据（如状态快照、配置）

## 验证
- TC-OPENAMP-001: 1000 次消息延迟分布
- TC-OPENAMP-002: R5 重启后自动重连
