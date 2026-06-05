---
id: SYS-REQ-001
title: 4 路 4K@30fps 视频同步接入
type: requirement-system
status: verified
owner: fpga-team
version: 1.0
created: 2026-06-04
updated: 2026-06-04
priority: P0
traces:
  up: [STK-REQ-001]
  down: [DES-ARCH-001, DES-ARCH-007, IF-REQ-001, MOD-HLS-ISP, MOD-C-FRAME-MGR, TC-CAM-001]
tags: [system, video, capture]
verification_method: integration_test
---

# SYS-REQ-001: 4 路 4K@30fps 视频同步接入

## 描述
设备应能同步接收 4 路 Sony IMX415 摄像头的 4K@30fps RAW10 视频流，经 ISP 处理后写入 DDR4 帧缓冲，供后续 DPU 推理使用。

## 接口
- 物理：MIPI CSI-2 4-lane × 4 路
- 格式：RAW10 → NV12（YUV420）
- 帧率：30fps × 4 路
- 同步：4 路帧间偏差 < 5ms

## 验收准则
1. 4 路连续采集 24h 无丢帧
2. NV12 输出分辨率 1920×1080
3. 帧间偏差 < 5ms
4. 单路延迟 < 66ms（2 帧）
5. CPU 占用率 < 5%（ISP 卸载到 PL）

## 带宽估算
- 输入：4 × 3840×2160 × 30 × 10bit ≈ 9.96 Gbps
- 输出：4 × 1920×1080 × 30 × 12bit ≈ 2.99 Gbps
- DDR4 写入：约 373 MB/s

## 验证
- TC-CAM-001: 4 路摄像头长稳测试
- TC-CAM-002: 帧间同步精度测试
- TC-CAM-003: 24h 丢帧率测试

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-06-04 | li.si | 初始 |
