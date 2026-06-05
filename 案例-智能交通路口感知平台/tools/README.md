---
id: tools-readme
title: 工具流（sw_hw_toolflow）
type: project-tooling
status: active
version: 1.0
---

# 工具流（sw_hw_toolflow）

> 跨项目可迁移的自动化工具流，对应本项目 `core/` 核心部分。
> 详见根目录 [ARCHITECTURE.md](../ARCHITECTURE.md) §4。

## 目录速览

```
tools/
├── sw_hw_toolflow/              # Python 库
│   ├── core/                    # 核心脚本（追溯/校验/打包）
│   ├── adapters/                # 工具链适配器（Vivado/HLS/MATLAB/...）
│   ├── pipelines/               # 端到端流水线
│   └── cli/                     # 命令行入口
├── hooks/                       # Git hooks 模板
├── make/                        # Makefile 片段
├── schemas/                     # JSON Schema
├── ci-templates/                # CI 平台模板
├── agents/                      # LLM Agent 模板
└── tests/                       # 工具自身测试
```

## 快速开始

```bash
# 安装工具流
pip install -e tools/

# 初始化新项目
sw-htf init my-project --template edgevision-t1

# 追溯检查
sw-htf trace check --strict

# 全链路验证
sw-htf verify full

# 工具链配置
sw-htf toolchain show
```

## 主要命令

| 命令 | 说明 |
|------|------|
| `sw-htf trace` | 追溯矩阵生成/校验/查询 |
| `sw-htf verify` | 单元/模块/集成/全链路/工厂 |
| `sw-htf build` | C/HLS/RTOS/AI/综合 |
| `sw-htf sim` | HDL 仿真、Co-simulation |
| `sw-htf codegen` | 算法→C/HDL 代码生成 |
| `sw-htf ai` | 训练/量化/部署 |
| `sw-htf release` | OTA 包构建与签名 |
| `sw-htf toolchain` | 工具链配置管理 |
| `sw-htf init` | 模板项目初始化 |

## 与 core/ 的关系

- **核心部分 `core/`** —— 纯文本真相（git 是版本库）
- **工具流 `tools/`** —— 自动化执行器（可独立升级/复用）
- **绑定** —— `configs/toolchain.yml` 告诉工具流"项目用哪个版本"
- **生成** —— 工具流读 core/ → 产出构建/报告/索引

## 跨项目迁移

1. 复制 `core/` 模板 → 改 `00_MANIFEST/requirements.yml`
2. 复制 `configs/` → 改 `toolchain.yml`
3. 复用 `tools/`（子模块/包安装）
4. 工具流版本由 SemVer 管理，可与项目独立升级

## 关键设计

- 工具流**不写**核心部分的状态——只读不写（避免覆盖人工修改）
- 工具流**生成物**（构建产物、报告）走 `core/04_IMPLEMENTATION/*/build/`、`.runs/`、gitignore
- 工具流**入口**固定为 `sw-htf <verb> <noun> ...`
- 工具流**CI 集成**通过 `tools/ci-templates/{github,gitlab}.yml`

## 详细文档

- [ARCHITECTURE.md §4](../ARCHITECTURE.md) — 工具流设计
- `tools/sw_hw_toolflow/core/` — 核心脚本
- `tools/agents/` — LLM Agent 模板
- `tools/ci-templates/` — CI 平台模板
