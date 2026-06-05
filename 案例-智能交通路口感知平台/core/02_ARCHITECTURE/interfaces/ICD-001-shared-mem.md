---
id: ICD-001
title: PS↔PL 共享内存 (DetectionResult)
type: interface-control
status: approved
owner: architect-team
version: 1.0
traces: { up: [DES-ARCH-001], down: [MOD-C-INFER, MOD-C-OSD] }
tags: [interface, shared-memory, detection]
---

# ICD-001: PS↔PL 共享内存 (DetectionResult)

## 数据结构

```c
// 4 字节对齐
typedef struct {
    uint32_t frame_id;
    uint64_t timestamp_us;
    uint8_t  channel;        // 摄像头通道 0-3
    uint8_t  object_count;
    uint8_t  reserved[2];
    struct {
        uint8_t  class_id;   // 0=car, 1=truck, 2=bus, 3=person, 4=plate
        float    confidence; // 0.0-1.0
        uint16_t x, y;       // bbox 左上角像素坐标
        uint16_t w, h;       // bbox 宽高
        uint8_t  track_id;   // ByteTrack ID
        char     plate[12];  // 车牌（如识别到）
    } objects[64];
} DetectionResult_t;
```

## 内存布局

- 4 路独立环形缓冲区
- 每路 3 个槽位（双缓冲+1）
- 总大小：4 × 3 × sizeof(DetectionResult_t) ≈ 12 KB

## 同步机制

- 每路使用 1 个内存屏障变量
- PL 写完成 → 置 1
- PS 读完成 → 置 0

## 验证
- TC-ICD-001: 多线程读写无撕裂
- TC-ICD-002: 64 目标上限测试
