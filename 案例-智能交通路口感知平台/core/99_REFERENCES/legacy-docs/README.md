# 历史文档（已结构化抽取）

> 原 `docs/01-08` 与 `docs/仿真验证指南.md` 的内容已经按本架构（[ARCHITECTURE.md](../../../../ARCHITECTURE.md)）
> 抽取到 `core/01_REQUIREMENTS/`、`core/02_ARCHITECTURE/`、`core/05_VERIFICATION/` 等位置。
> 本目录保留原文作为历史与可追溯参考。

## 索引

| 旧文件                                              | 抽取到                                                           |
| --------------------------------------------------- | ---------------------------------------------------------------- |
| docs/01-需求与架构.md                                | `core/01_REQUIREMENTS/` + `core/02_ARCHITECTURE/` + `core/02_ARCHITECTURE/views/development/` |
| docs/02-FPGA硬件开发.md                              | `core/02_ARCHITECTURE/views/physical/` + `core/04_IMPLEMENTATION/hls/` + `core/04_IMPLEMENTATION/verilog/` |
| docs/03-AI模型开发.md                                | `core/04_IMPLEMENTATION/ai/` + `core/01_REQUIREMENTS/system/SYS-REQ-002/003` |
| docs/04-嵌入式软件开发.md                            | `core/04_IMPLEMENTATION/c/` + `core/04_IMPLEMENTATION/rtos/` + `core/04_IMPLEMENTATION/proto/` |
| docs/05-实时控制开发.md                              | `core/01_REQUIREMENTS/system/SYS-REQ-006` + `core/02_ARCHITECTURE/decomposition/DES-ARCH-005/` + `core/04_IMPLEMENTATION/rtos/` |
| docs/06-云端与通信.md                                | `core/04_IMPLEMENTATION/proto/` + `core/02_ARCHITECTURE/interfaces/ICD-003/004/` + `core/04_IMPLEMENTATION/bindings/web/` |
| docs/07-安全与量产.md                                | `core/01_REQUIREMENTS/safety/` + `core/01_REQUIREMENTS/verification/VP-003/` |
| docs/08-商业化路径.md                                | `core/00_MANIFEST/stakeholders.md` + `core/07_FEEDBACK/adr/` + `core/06_INTEGRATION/` |
| docs/仿真验证指南.md                                 | `core/05_VERIFICATION/integration/` + `core/03_ALGORITHM/simulation/` |

> 旧文档与新结构可能存在不一致，**以新结构为准**。
