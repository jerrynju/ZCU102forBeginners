---
id: TR-002
title: 国产 FPGA 替代
type: trade-study
status: draft
owner: architect-team
version: 0.1
traces: { up: [DES-ARCH-001], down: [] }
tags: [trade-study, supply-chain, fpga]
---

# TR-002: 国产 FPGA 替代（草案）

## 背景
受贸易限制影响，Xilinx Zynq UltraScale+ 系列存在供应链风险。需评估国产替代方案。

## 候选

| 厂家 | 型号 | 工艺 | 性能 | AI 加速 | 状态 |
|------|------|------|------|---------|------|
| 复旦微 | FMQL100TAI | 28nm | 较 ZU9EG 弱 | 需自研 NPU IP | 验证中 |
| 紫光同创 | Logos PGL50H | 28nm | 资源较少 | 需外接 | 已流片 |
| 安路科技 | SALVAGE-L | 28nm | 入门 | 需外接 | 量产 |

## 关键差距

1. **AI 推理性能**：DPU B4096 是经过优化的成熟 IP，国产替代需 1-2 年才能达到等价算力
2. **工具链成熟度**：Vitis/Vivado vs 国产 EDA，差距明显
3. **HLS 生态**：Vitis HLS 高度优化，国产 HLS 工具尚不成熟
4. **IP 库**：Xilinx 拥有完整生态（MPSoC、DPU、MIPI、10GbE），国产需自研/集成

## 结论
**短期（1-2 年）**：维持 Xilinx 方案，确保量产；建立国产替代实验室，跟踪复旦微
**中期（2-3 年）**：在边缘计算要求较低的场景试点国产方案
**长期（3-5 年）**：随着国产工艺和工具链成熟，切换主供应商

## 后续行动
- [ ] 复旦微 FM-MPSOC 评估板采购
- [ ] DPU 等价 NPU IP 自研可行性研究
- [ ] 供应链风险管理：库存策略、订货 lead time
