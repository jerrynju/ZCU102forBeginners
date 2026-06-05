---
id: DES-ARCH-007
title: ISP 流水线
type: design-architecture
status: approved
owner: fpga-team
version: 1.0
traces: { up: [SYS-REQ-001, PERF-REQ-001], down: [MOD-HLS-ISP] }
tags: [architecture, isp, hls]
---

# DES-ARCH-007: ISP 流水线

## 功能阶段

1. **黑电平校正**（BLC）：减去暗电流偏置
2. **去马赛克**（Demosaicing）：RGGB Bayer → RGB
3. **白平衡**（AWB）：色彩校正
4. **伽马校正**：线性 → sRGB
5. **色彩空间转换**（CSC）：RGB → YUV
6. **缩放**（Resize）：4K → 1080p（供 DPU）

## 流水线设计

- 4 路 ISP 并行例化（每路独立 AXI-Stream）
- 帧级 DATAFLOW 流水线
- 像素级 PIPELINE II=1
- 行缓冲 BRAM 优化

## 接口

- 输入：AXI-Stream RAW10 @ 4K@30fps
- 输出：AXI-Stream NV12 @ 1080p@30fps
- 控制：AXI-Lite（白平衡参数、黑电平、resize 比例）

## 资源

| 指标 | 目标 | 单路实测 |
|------|------|---------|
| 时钟 | 250 MHz | 250 MHz |
| 延迟 | < 2 帧 | ~66ms |
| LUT | < 15K | ~13K |
| DSP | < 50 | ~40 |
| BRAM | < 20 | ~18 |

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | li.si | 初始 |
