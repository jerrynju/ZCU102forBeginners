# 变更日志

所有对 `core/`、`configs/`、`tools/` 显著变更均需记录在此。
格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### Added
- 建立 `core/` 7 段流水线结构
- 建立 `tools/` 工具流骨架
- 完整 `ARCHITECTURE.md` 架构宪法
- 全量需求文档（STK-REQ, SYS-REQ, IF-REQ, PERF-REQ, SAF-REQ, VP-）
- 全量架构文档（DES-ARCH, ICD, TR, CON-OP）
- 追溯矩阵 `traceability.yml`
- 工具链配置 `configs/toolchain.yml`
- 决策记录 ADR-001/002/003

### Changed
- 旧 `docs/01-08` → `core/99_REFERENCES/legacy-docs/` 历史保留
- 旧 `ai/` → `core/04_IMPLEMENTATION/ai/{train,quantization,models,deploy}`
- 旧 `hardware/` → `core/04_IMPLEMENTATION/{hls,verilog}`
- 旧 `software/` → `core/04_IMPLEMENTATION/{c,proto,rtos}`
- 旧 `sim/` → `core/03_ALGORITHM/simulation/src`
- 旧 `tests/` → `core/05_VERIFICATION/integration`
- 旧 `scripts/` → `core/06_INTEGRATION/ci-cd`
- 旧 `website/` → `core/04_IMPLEMENTATION/bindings/web`

### Removed
- 无

## [0.1.0] - 2026-06-04

### Added
- 项目初始化（来自 ZCU102 商业闭环开发流程）
- 8 篇旧 docs/ 设计文档
- YOLOv8 + LPRNet 训练/量化/部署脚本
- Vitis HLS ISP / OSD 实现
- FreeRTOS R5 信号灯控制
- MQTT/gRPC 云端通信
- 工厂测试脚本
- Vue Web 管理界面
- Python 算法仿真（场景/检测/跟踪/事件）
