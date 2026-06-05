---
id: TR-001
title: PS/PL 划分（ISP、AI 推理、跟踪、信号灯）
type: trade-study
status: approved
owner: architect-team
version: 1.0
traces: { up: [DES-ARCH-001], down: [] }
tags: [trade-study, ps-pl-split]
---

# TR-001: PS/PL 划分

## 候选方案

| 方案 | ISP | AI 推理 | 跟踪 | 信号灯 |
|------|-----|---------|------|--------|
| A | PL | PL DPU | PS A53 | PS R5 |
| B | PL | PS A53 (CPU) | PS A53 | PS A53 |
| C | PL | PL DPU | PL (HLS) | PS R5 |
| D | PS A53 | PS A53 | PS A53 | PS R5 |

## 评估矩阵

| 方案 | 性能 | 资源 | 灵活性 | 实时性 | 开发成本 | 总分 |
|------|------|------|--------|--------|----------|------|
| A | ★★★★★ | ★★★★ | ★★★★ | ★★★★★ | ★★★ | **★★★★★** |
| B | ★★ | ★★★★★ | ★★★★★ | ★★★ | ★★★★★ | ★★★ |
| C | ★★★★★ | ★★ | ★★ | ★★★★★ | ★★ | ★★★ |
| D | ★★ | ★★★★★ | ★★★★★ | ★★★★ | ★★★★ | ★★★ |

## 决策

**采用方案 A**：
- ISP 在 PL（HLS）— 4 路并行吞吐 > 10 GB/s
- AI 推理在 PL（DPU）— 固定算子，资源利用率 > 90%
- 跟踪在 PS A53 — 数据相关算法，软件灵活迭代
- 信号灯在 PS R5 — 硬实时 < 10ms

## 结论
方案 A 在性能、实时性、资源利用率上都最优，开发成本通过 Vitis HLS + Vitis AI 工具链降低。
