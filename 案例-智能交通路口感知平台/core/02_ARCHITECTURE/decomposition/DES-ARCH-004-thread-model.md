---
id: DES-ARCH-004
title: 主控线程模型
type: design-architecture
status: approved
owner: architect-team
version: 1.0
traces: { up: [PERF-REQ-001], down: [MOD-C-MAIN] }
tags: [architecture, threading, software]
---

# DES-ARCH-004: 主控线程模型（A53 Linux）

## 线程清单

| 线程 | 数量 | 优先级 | 职责 |
|------|------|--------|------|
| capture | 4 | SCHED_FIFO 80 | 各路 V4L2 帧采集 |
| infer | 1 | SCHED_FIFO 70 | DPU 推理（轮询 4 路）|
| reporter | 1 | SCHED_OTHER | MQTT 异步上报 |
| grpc | 1 | SCHED_OTHER | gRPC 管理服务 |
| rest | 1 | SCHED_OTHER | REST + WebSocket |
| watchdog | 1 | SCHED_FIFO 90 | A53↔R5 心跳 |

## 数据流

```
V4L2 cap[0..3] → frame_queue[0..3] → infer_thread
                                          ↓
                                     EventDetector
                                          ↓
                              events_queue → reporter_thread → MQTT
                                          ↓
                                     OSD Writer → PL 寄存器
```

## 帧队列设计

- 每路 3 帧循环队列（双缓冲+1）
- 零拷贝：`mmap()` 直接映射 VDMA 物理地址
- 超时 50ms：推理线程跳过空帧

## 同步原语

- `frame_queue[ch]`：`std::shared_ptr<Frame>` + `std::condition_variable`
- `events_queue`：`std::lockfree::queue<Event>`（boost 或 moodycamel）
- 配置热更新：`std::atomic<Config*>` 指针切换

## 异常处理

- 推理线程崩溃：watchdog 自动重启
- 4G 摄像头掉线：3 次重连失败后切换备用
- 推理延迟 > 100ms：降级到 YOLOv8n 减小负载
