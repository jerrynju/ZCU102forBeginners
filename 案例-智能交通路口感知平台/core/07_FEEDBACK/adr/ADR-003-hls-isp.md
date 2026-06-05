---
id: ADR-003
title: ISP 采用 Vitis HLS 实现
type: adr
status: accepted
owner: architect-team
version: 1.0
created: 2026-06-04
traces: { up: [], down: [DES-ARCH-007, SYS-REQ-001, PERF-REQ-001] }
tags: [decision, isp, hls]
---

# ADR-003: ISP 采用 Vitis HLS 实现

## 状态
已接受（2026-06-04）

## 背景
4 路 4K ISP 像素率总计 24 Gbps，需要并行流处理。可选实现：
- Vitis HLS（C++ 高层次综合）
- 手工 RTL（Verilog/VHDL）
- 商业 ISP IP（Cadence / Synopsys）

## 决策
**采用 Vitis HLS（C++ 高层次综合）**

## 理由
1. **迭代速度**：C++ 描述比 RTL 快 5-10x
2. **可维护性**：算法变更无需重写 RTL
3. **资源优化**：HLS 工具自动调度、流水化
4. **成本**：免费（Vitis HLS），商业 IP 数十万美元

## 取舍
- 代价：HLS 资源利用率略低于手工 RTL（约 80-90% 水平）
- 替代方案：手工 RTL（更优资源但开发成本高）
- 备选方案：商业 IP（最优性能但需授权）

## 后果
- 需要 Vitis HLS 工具链（vitis_hls）
- HLS 工程师需掌握 pragma 调优
- 仿真需 C 测试平台 + RTL 协同仿真

## 验证
- TC-IF-MIPI-002: 4 lane 同步测试
- TC-CAM-001: 4 路 24h 丢帧测试

## 关联
- 受影响需求：SYS-REQ-001, PERF-REQ-001
- 受影响设计：DES-ARCH-007
- 受影响实现：MOD-HLS-ISP
