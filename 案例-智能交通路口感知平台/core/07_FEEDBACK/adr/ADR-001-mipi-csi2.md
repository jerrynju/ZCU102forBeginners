---
id: ADR-001
title: 采用 MIPI CSI-2 4-lane 摄像头接口
type: adr
status: accepted
owner: architect-team
version: 1.0
created: 2026-06-04
traces: { up: [], down: [DES-ARCH-001, IF-REQ-001] }
tags: [decision, video, interface]
---

# ADR-001: 采用 MIPI CSI-2 4-lane 摄像头接口

## 状态
已接受（2026-06-04）

## 背景
智能路口需要部署 4 路 4K 摄像头，每路像素率 2.5 Gbps/lane。可选接口：
- MIPI CSI-2 4-lane（2.5 Gbps/lane）
- USB3 Vision (UVC)
- GigE Vision (1 GbE / 10 GbE)
- Camera Link（淘汰）

## 决策
**采用 MIPI CSI-2 4-lane × 4 路**

## 理由
1. **带宽**：2.5 Gbps/lane × 4 = 10 Gbps/路，远超 USB3 / 1GbE
2. **延迟**：MIPI 硬件直达 FPGA，无协议开销（~ms 级 vs USB3 的 100ms+）
3. **成本**：传感器直连 FMC 子板，无独立相机成本
4. **同步精度**：4 路硬件同步，PPS 触发，帧间偏差 < 5ms
5. **功耗**：MIPI PHY < 100mW/lane，优于 USB3

## 取舍
- 代价：定制 FMC 子板（一次性 NRE ~¥20k）
- 替代方案：USB3 摄像头（无 NRE，但延迟高 / 带宽低）

## 后果
- 需自研或采购 MIPI CSI-2 RX IP（Xilinx MIPI CSI-2 RX Subsystem）
- 摄像头选型受限（IMX415 / IMX477 等）
- 线缆长度 < 30cm（板内）

## 验证
- TC-IF-MIPI-001: 单 lane 拉偏测试
- TC-IF-MIPI-002: 4 lane 同步测试

## 关联
- 受影响需求：SYS-REQ-001, PERF-REQ-001
- 受影响设计：DES-ARCH-001
- 受影响接口：IF-REQ-001
