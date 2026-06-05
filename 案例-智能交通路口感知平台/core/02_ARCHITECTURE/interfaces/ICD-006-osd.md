---
id: ICD-006
title: OSD 寄存器接口
type: interface-control
status: approved
owner: fpga-team
version: 1.0
traces: { up: [DES-ARCH-007, IF-REQ-005], down: [MOD-HLS-OSD] }
tags: [interface, osd, register]
---

# ICD-006: OSD 寄存器接口（PL 寄存器映射）

## 寄存器列表

| Offset | Name | Type | 说明 |
|--------|------|------|------|
| 0x00 | CTRL | RW | bit0: enable, bit1: clear |
| 0x04 | BOX_COUNT | RW | 检测框数量（0-64）|
| 0x08 | BOX_BASE | RW | 检测框数组基地址（DDR）|
| 0x0C | FRAME_W | R | 帧宽度 |
| 0x10 | FRAME_H | R | 帧高度 |

## 检测框结构（DDR 中）

```c
typedef struct {
    uint16_t x, y;
    uint16_t w, h;
    uint8_t  class_id;
    uint8_t  confidence;  // 0-100
} OSD_Box_t;
```

## 写流程（PS→PL）

1. PS 准备 64 个 OSD_Box_t 数组写入 DDR（mmap 到 0x90000000 区域）
2. PS 写 BOX_BASE = DDR 物理地址
3. PS 写 BOX_COUNT = N
4. PS 写 CTRL = 0x1（enable）

PL OSD IP 自动从 DDR 读检测框，叠加到视频流。
