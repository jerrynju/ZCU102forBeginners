---
id: ALG-TH-ISP-001
title: ISP 流水线理论
type: algorithm-theory
status: approved
owner: fpga-team
version: 1.0
traces: { up: [DES-ARCH-007, SYS-REQ-001], down: [] }
tags: [algorithm, isp, theory]
---

# ALG-TH-ISP-001: ISP 流水线理论

## Bayer Pattern

Sony IMX415 输出 Bayer pattern（RGGB）：
```
R G R G ...
G B G B ...
R G R G ...
...
```

每个像素只有 1 个颜色分量。

## 6 步流水线

### 1. 黑电平校正 (BLC)
RAW 像素值 = 实际信号 + 暗电流偏置
BLC 减去黑电平值（约 64-256，由传感器手册给出）。

### 2. 去马赛克 (Demosaicing)
Bayer RGGB → 完整 RGB。常用算法：
- 双线性插值（最简单，硬件友好）
- 边缘导向插值（更好，FPGA 中需 1 行延迟）
- Malvar-He-Cutler（学术，5x5 卷积）

### 3. 自动白平衡 (AWB)
灰度世界假设：图像平均色 = 中性灰。
增益因子：R/G, B/G 由图像统计计算。

### 4. 伽马校正 (Gamma)
sRGB 曲线：`V_out = V_in^(1/2.2)`（近似）
使用 256 项 LUT 加速。

### 5. 色彩空间转换 (CSC)
RGB → YUV（ITU-R BT.601）：
```
Y  = 0.299R + 0.587G + 0.114B
U  = -0.1687R - 0.3313G + 0.5B + 128
V  = 0.5R - 0.4187G - 0.0813B + 128
```

### 6. 双线性缩放 (Resize)
4K (3840×2160) → 1080p (1920×1080)
2x 降采样（每 2 像素取 1）。

## HLS 实现要点

- **数据流级别 (DATAFLOW)**：函数级并行
- **像素级 (PIPELINE II=1)**：每个时钟 1 像素
- **行缓冲**：BRAM 存储 2 行原始数据
- **片上 RAM**：用于白平衡增益、伽马 LUT

## 参考

- Xilinx Vitis Vision Library
- "Digital Image Processing" Gonzalez & Woods
