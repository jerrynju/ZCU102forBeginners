# 进程/时序视图

> 4+1 视图中的动态视图，关注 **进程、时序、状态变化**。

## 端到端数据流时序

```
  时间(ms)   0    10    20    30    40    50    60
             │    │     │     │     │     │     │
  Camera     ├────┴─────┴─────┴─────┴─────┴─────┤  曝光 8ms
             │                                │
  MIPI RX    ├────┴─────┴─────┴─────┴─────┴────┤  接收 ~3ms
             │                              │
  ISP        ├────┴─────┴─────┴─────┴─────┴──┤  处理 ~2ms
             │                            │
  DDR 写入   ├──┴────┴────┴────┴────┴────┴──┤  VDMA ~1ms
             │                          │
  DPU 推理   │         ├────┴─────┴─────┴────┤  ~18ms (YOLOv8s)
             │         │              │
  跟踪/事件  │         │      ├──┴────┴──┤   ~2ms
             │         │      │     │
  OSD 写入   │         │      ├────┴──┤     ~1ms
             │         │      │    │
  MQTT 上报  │         │      ├────┴────┴──┤  ~50ms
```

## 主循环时序（A53 Linux）

```cpp
// capture_thread (per channel) - 优先级 80
while (running) {
    frame = cap.dqbuf();              // 阻塞
    frame_queue[ch].push(frame);      // 通知 infer
}

// infer_thread - 优先级 70
while (running) {
    for (ch in 0..3) {
        frame = frame_queue[ch].pop(timeout=50ms);
        if (!frame) continue;
        result = infer_engine.run(frame);  // DPU + tracking + event
        osd_writer.write(ch, result);
        if (events) reporter.enqueue(events);
    }
}

// reporter_thread - 优先级 OTHER
while (running) {
    event = queue.pop();
    publisher.publish(event);            // MQTT + OSS upload
}

// grpc_thread - 优先级 OTHER
server.run();                            // 阻塞
```

## 状态机

### 信号灯状态机（R5 FreeRTOS）

参见 [DES-ARCH-005](../decomposition/DES-ARCH-005-r5-tasks.md)

```
PHASE_NS_GREEN ──45s──→ PHASE_NS_YELLOW ──3s──→ PHASE_EW_GREEN ──45s──→ ...
                              │
                              └── A53 命令 → PHASE_NS_LEFT 等

故障 → PHASE_ALLRED
```

### 事件检测状态机

参见 [DES-ARCH-009](../decomposition/DES-ARCH-009-event-detector.md)

### OTA 升级状态机

```
NORMAL ──下载 swu──→ DOWNLOADING ──验签──→ VERIFYING
                                            │
                                            ├─ 成功 → INSTALLING ──切换分区──→ REBOOTING ──启动──→ NEW_VERSION
                                            └─ 失败 → ROLLBACK (旧版本)
```

## 关键时序指标

| 指标 | 预算 | 验收 |
|------|------|------|
| 单帧端到端 | < 30ms | ~22ms |
| CAN 指令延迟 | < 10ms | ~5ms |
| 云端事件延迟 | < 500ms | ~200ms |
| 状态机切换 | 10ms 周期 | 10ms |
