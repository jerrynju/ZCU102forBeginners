---
id: DES-ARCH-002
title: 存储器分区方案
type: design-architecture
status: approved
owner: architect-team
version: 1.0
traces: { up: [PERF-REQ-005], down: [] }
tags: [architecture, memory]
---

# DES-ARCH-002: 存储器分区方案

## DDR4 4GB 分区（A53 Linux 视角）

```
0x0000_0000 ~ 0x7FFF_FFFF  (2GB)   - Linux OS + 应用程序 + 堆栈
0x8000_0000 ~ 0x8FFF_FFFF  (256MB) - 视频帧缓冲区（4路×3帧×1080p NV12）
0x9000_0000 ~ 0x97FF_FFFF  (128MB) - DPU 输入/输出缓冲
0x9800_0000 ~ 0x9FFF_FFFF  (128MB) - AI 模型权重（预加载）
0xA000_0000 ~ 0xAFFF_FFFF  (256MB) - H.264 编码缓冲区
0xB000_0000 ~ 0xBFFF_FFFF  (256MB) - R5 OpenAMP 共享内存（ECC 保护）
0xC000_0000 ~ 0xFFFF_FFFF  (1GB)   - 预留 / 未来扩展
```

R5 TCM (256KB) - FreeRTOS 内核 + 实时任务栈

## 设备树 reserved-memory

```dts
reserved-memory {
    #address-cells = <2>;
    #size-cells = <2>;
    ranges;

    video_buf: buffer@80000000 {
        reg = <0x0 0x80000000 0x0 0x0C000000>;
        no-map;
    };
    dpu_buf: buffer@8C000000 {
        reg = <0x0 0x8C000000 0x0 0x08000000>;
        no-map;
    };
    rpu_buf: buffer@B8000000 {
        reg = <0x0 0xB8000000 0x0 0x08000000>;
        no-map;
    };
};
```

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | architect | 初始 |
