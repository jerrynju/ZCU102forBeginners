---
id: DES-ARCH-005
title: R5 FreeRTOS 任务划分
type: design-architecture
status: approved
owner: rtos-team
version: 1.0
traces: { up: [SYS-REQ-006, SAF-REQ-002, SAF-REQ-003, IF-REQ-003, IF-REQ-006], down: [TASK-WATCHDOG, TASK-CAN-RX, TASK-SIG-FSM, TASK-OPENAMP, TASK-PPS-SYNC] }
tags: [architecture, rtos, freertos]
---

# DES-ARCH-005: R5 FreeRTOS 任务划分

## 任务清单

| 任务 | 优先级 | 栈 (words) | 周期 | 职责 |
|------|--------|------------|------|------|
| task_watchdog | 5 | 256 | 100ms | A53 心跳监控 + 硬件 WDT |
| task_can_rx | 4 | 512 | event | CAN 接收与处理 |
| task_signal_fsm | 3 | 1024 | 10ms | 信号灯状态机 |
| task_openamp | 2 | 512 | event | RPMsg 接收 |
| task_pps_sync | 2 | 256 | event | PPS 时间同步 |
| task_telemetry | 1 | 256 | 1s | 遥测数据上报 |

## 任务间通信

| 资源 | 类型 | 用途 |
|------|------|------|
| `q_can_rx_msg` | Queue | CAN 接收消息 |
| `q_ctrl_cmd` | Queue | A53→R5 控制指令 |
| `sem_pps` | Semaphore | PPS 时间同步信号 |

## 周期精度

- 状态机：10ms 周期（vTaskDelayUntil）
- WDT 喂狗：100ms
- 心跳：1s

## 内存

- R5 TCM：256KB
- 任务栈总占用：~30KB
- 内核 + 队列：~50KB
- 剩余 ~170KB 给应用

## 故障处理

- task_watchdog 监控其他任务心跳（每任务发 vTaskSuspend 计数）
- 任意任务 3 个周期未运行 → 系统复位
