---
id: ICD-002
title: R5↔A53 RPMsg 协议
type: interface-control
status: approved
owner: rtos-team
version: 1.0
traces: { up: [DES-ARCH-006], down: [TASK-OPENAMP, MOD-C-OPENAMP] }
tags: [interface, openamp, rpmsg]
---

# ICD-002: R5↔A53 RPMsg 协议

参见 [DES-ARCH-006](../decomposition/DES-ARCH-006-openamp.md)

## 帧结构

```c
typedef struct __attribute__((packed)) {
    uint8_t  type;          // MSG_TYPE_*
    uint8_t  seq;           // 序列号（0-255 循环）
    uint16_t length;        // payload 长度
    uint8_t  payload[60];   // 实际数据
} RPMsgFrame_t;
```

## 消息清单

| Type | 名称 | 方向 | Payload |
|------|------|------|---------|
| 0x01 | MSG_TYPE_CTRL_CMD | A53→R5 | CtrlCmd_t |
| 0x02 | MSG_TYPE_PHASE_QUERY | A53→R5 | - |
| 0x03 | MSG_TYPE_STATUS_RESP | R5→A53 | SignalStatus_t |
| 0x04 | MSG_TYPE_COUNT_REPORT | R5→A53 | CountReport_t |
| 0xFF | MSG_TYPE_HEARTBEAT | 双向 | - |

## CtrlCmd_t

```c
typedef struct {
    uint8_t  type;          // CMD_PHASE_OVERRIDE / CMD_FORCE_ALLRED / CMD_SET_ADAPTIVE
    uint8_t  phase;         // SignalPhase_t
    uint16_t duration_ms;
} CtrlCmd_t;
```

## CountReport_t

```c
typedef struct {
    uint64_t timestamp;
    uint32_t counts[4][6];  // [direction][class_id]
} CountReport_t;
```
