# 软硬件协同开发文件组织架构

> 版本：v1.0 · 最后更新：2026-06-04 · 状态：active · 维护者：架构组

本文档是项目全生命周期的**架构宪法**。所有目录命名、文件命名、ID 规范、追溯约定、工具流职责
均以本文档为准；任何偏离需经 ADR（架构决策记录）正式记录。

本架构由两部分组成：

- **核心部分（`core/`）** —— 纯文本（Markdown + YAML + 源码），git 友好，LLM/Agent 友好。
- **工具流（`tools/`）** —— 可迁移的自动化流水线，绑定具体工具链，跨项目复用。

两个部分通过 **`configs/toolchain.yml`** 适配，配合 **`core/00_MANIFEST/`** 的元数据实现
"核心/工具解耦"：项目数据可独立演化，工具流可独立升级。

---

## 0. 架构顶层视图

```
+---------------------------------------------------------------------------+
|                          项目仓库（git submodule friendly）                 |
|                                                                           |
|  +-------------------------+   +----------------------+   +------------+  |
|  |   core/  (核心部分)     |<->|  tools/  (工具流)    |<->| configs/   |  |
|  |   纯文本、git 友好      |   |  可迁移、配置驱动     |   | 项目配置   |  |
|  +-------------------------+   +----------------------+   +------------+  |
|         ^                              ^                                  |
|         |                              |                                  |
|     LLM/Agent                     工具链适配器                            |
|     人/团队                       (MATLAB/Vivado/gcc...)                   |
+---------------------------------------------------------------------------+
```

---

## 1. 设计原则

| 原则                | 落地手段                                                            |
| ------------------- | ------------------------------------------------------------------- |
| **纯文本优先**      | 全部需求/架构/接口/决策用 Markdown + YAML；模型与代码以源码为准   |
| **约定优于配置**    | 强制 ID 命名、目录、文件命名规范；违规由工具流校验拦截              |
| **双向可追溯**      | 需求↔设计↔实现↔测试双向链接；机器可读（YAML）+ 人类可读（Markdown）双轨 |
| **核心与工具解耦**  | `core/` 只描述"是什么"，`tools/` 只描述"怎么做"                    |
| **LLM/Agent 友好**  | 提供 INDEX、MANIFEST、requirements.yml 等结构化入口                 |
| **Git 友好**        | 强制 LF、`.gitattributes` 区分文本/二进制、LFS 管大文件             |
| **可迁移**          | 工具流以独立仓库存在，跨项目通过 `toolchain.yml` 适配               |
| **状态机驱动**      | 每条需求/设计/代码带 `status` 字段，状态机统一                       |
| **可计量**          | `traceability.yml` 提供量化指标（覆盖率、漂移、缺陷逃逸）           |
| **留痕即文档**      | 关键决策、问题、复盘一律文本化，git 历史 = 项目历史                  |

---

## 2. 核心部分（`core/`）

### 2.1 顶层目录

```
core/
├── 00_MANIFEST/                 # 入口与元数据（LLM/Agent 首选读取）
├── 01_REQUIREMENTS/             # 需求管理
├── 02_ARCHITECTURE/             # 系统架构建模
├── 03_ALGORITHM/                # 算法设计（实现前）
├── 04_IMPLEMENTATION/           # 代码生成与实现
├── 05_VERIFICATION/             # 功能测试与验证
├── 06_INTEGRATION/              # 集成与部署
├── 07_FEEDBACK/                 # 迭代与反馈
└── 99_REFERENCES/               # 外部参考资料 + 历史文档
```

### 2.2 详细目录结构

```
core/
├── 00_MANIFEST/                 # 项目入口与元数据（LLM/Agent 首选）
│   ├── README.md                # 项目一句话定位 + 导航
│   ├── INDEX.md                 # 文档全索引（自动生成）
│   ├── INDEX.json               # 机器可读索引
│   ├── CHANGELOG.md             # 项目级变更日志
│   ├── requirements.yml         # 需求库（结构化）
│   ├── traceability.yml         # 追溯矩阵（结构化）
│   ├── glossary.md              # 术语表
│   ├── stakeholders.md          # 干系人列表
│   ├── metrics.yml              # 项目度量（缺陷/覆盖率/漂移）
│   └── decisions.log            # 关键决策日志（自动汇总 ADR）
│
├── 01_REQUIREMENTS/             # 需求管理
│   ├── stakeholder/             # 干系人需求  STK-REQ-XXX
│   ├── system/                  # 系统需求    SYS-REQ-XXX
│   ├── interface/               # 接口需求    IF-REQ-XXX
│   ├── performance/             # 性能需求    PERF-REQ-XXX
│   ├── safety/                  # 安全/可靠性  SAF-REQ-XXX
│   ├── regulatory/              # 法规/标准   REG-REQ-XXX
│   └── verification/            # 验证策略    VP-XXX
│
├── 02_ARCHITECTURE/             # 系统架构建模
│   ├── views/                   # 4+1 视图
│   │   ├── logical/             # 逻辑视图（模块、接口、关系）
│   │   ├── process/             # 进程/时序视图
│   │   ├── physical/            # 物理/部署视图
│   │   └── development/         # 开发视图（仓库、构建、测试）
│   ├── models/                  # 架构模型源（PlantUML/Mermaid）
│   ├── decomposition/           # 功能→模块→单元分解  DES-ARCH-XXX
│   ├── interfaces/              # 接口控制文档  ICD-XXX
│   ├── trade-studies/           # 权衡研究  TR-XXX
│   └── concept/                 # 概念图、运行场景  CON-OP-XXX
│
├── 03_ALGORITHM/                # 算法设计（实现前）
│   ├── theory/                  # 数学推导、论文笔记  ALG-TH-XXX
│   ├── simulation/              # MATLAB/Python 算法仿真
│   │   ├── src/                 # 仿真代码
│   │   ├── scripts/             # 仿真驱动脚本
│   │   ├── test/                # 算法单元测试
│   │   ├── data/                # 测试向量
│   │   ├── results/             # 仿真输出（gitignore）
│   │   └── figures/             # 图表
│   ├── golden-ref/              # 算法黄金参考（CI 比对基准）
│   └── metrics/                 # 精度/性能/资源度量报告
│
├── 04_IMPLEMENTATION/           # 代码生成与实现
│   ├── c/                       # C/C++ 实现
│   │   ├── src/                 # MOD-C-XXX.cpp / .c
│   │   ├── include/             # MOD-C-XXX.h
│   │   ├── test/                # C/C++ 单元测试
│   │   ├── build/               # 构建产物（gitignore）
│   │   ├── config/              # 编译配置
│   │   └── docs/                # Doxygen 源
│   ├── hls/                     # HLS 实现（C/RTL）
│   │   ├── isp_pipeline/
│   │   ├── osd_overlay/
│   │   └── codegen/             # HLS 工程 Tcl
│   ├── verilog/                 # HDL 实现
│   │   ├── rtl/                 # MOD-RTL-XXX.v / .sv / .vhd
│   │   ├── tb/                  # MOD-TB-XXX 测试平台
│   │   ├── sim/                 # 仿真脚本
│   │   ├── synth/               # 综合配置
│   │   ├── constraints/         # 时序/面积约束
│   │   ├── ip/                  # 第三方 IP 元数据
│   │   └── vivado_project/      # Vivado 工程文件
│   ├── ai/                      # AI 模型
│   │   ├── train/               # 训练脚本
│   │   ├── quantization/        # 量化脚本
│   │   ├── models/              # 模型定义
│   │   └── deploy/              # 部署产物（xmodel 等）
│   ├── rtos/                    # RTOS 实时代码
│   │   ├── src/                 # FreeRTOS 任务、驱动
│   │   └── config/              # 内核配置、链接脚本
│   ├── proto/                   # 接口协议定义（protobuf / flatbuf）
│   └── bindings/                # 语言绑定
│       └── web/                 # Web UI（Vue/HTML/JS）
│
├── 05_VERIFICATION/             # 功能测试与验证
│   ├── test-plans/              # 测试计划  TP-XXX
│   ├── test-cases/              # 测试用例  TC-XXX-XXX
│   ├── test-vectors/            # 输入/期望输出数据集
│   ├── testbenches/             # HDL/Co-simulation 测试平台
│   ├── reports/                 # 测试报告  TR-REP-XXX
│   ├── coverage/                # 覆盖率分析
│   ├── regressions/             # 回归测试集
│   └── integration/             # 端到端集成测试
│
├── 06_INTEGRATION/              # 集成与部署
│   ├── ci-cd/                   # CI/CD 流水线脚本
│   ├── environments/            # dev/sim/staging/prod 配置
│   ├── releases/                # 发布产物清单
│   └── deployment/              # 部署脚本与配置
│
├── 07_FEEDBACK/                 # 迭代与反馈
│   ├── issues/                  # 问题跟踪（文本化）ISS-XXX
│   ├── adr/                     # 架构决策记录  ADR-XXX
│   ├── reviews/                 # 设计/代码评审记录
│   ├── metrics/                 # 项目度量
│   └── retrospectives/          # 阶段/迭代回顾
│
└── 99_REFERENCES/               # 外部参考资料
    ├── papers/                  # 论文
    ├── standards/               # 标准
    ├── datasheets/              # 芯片手册
    └── legacy-docs/             # 历史文档（已结构化抽取）
```

### 2.3 ID 命名规范

| 类别            | 前缀          | 示例                | 文件命名                                      |
| --------------- | ------------- | ------------------- | --------------------------------------------- |
| 干系人需求      | `STK`         | `STK-REQ-001`       | `STK-REQ-001-user-auth.md`                    |
| 系统需求        | `SYS`         | `SYS-REQ-012`       | `SYS-REQ-012-latency.md`                      |
| 接口需求        | `IF`          | `IF-REQ-005`        | `IF-REQ-005-uart.md`                          |
| 性能需求        | `PERF`        | `PERF-REQ-003`      | `PERF-REQ-003-throughput.md`                  |
| 安全需求        | `SAF`         | `SAF-REQ-002`       | `SAF-REQ-002-watchdog.md`                     |
| 法规需求        | `REG`         | `REG-REQ-001`       | `REG-REQ-001-gdpr.md`                         |
| 设计/架构       | `DES`         | `DES-ARCH-007`      | `DES-ARCH-007-pipeline.md`                    |
| 接口控制        | `ICD`         | `ICD-003`           | `ICD-003-axi4.md`                             |
| 算法            | `ALG`         | `ALG-OFDM-001`      | `ALG-OFDM-001-equalizer.md`                   |
| 算法理论        | `ALG-TH`      | `ALG-TH-FFT-001`    | `ALG-TH-FFT-001-cooley-tukey.md`              |
| C/C++ 模块      | `MOD-C`       | `MOD-C-FFT-32`      | `fft32.cpp`                                   |
| RTL 模块        | `MOD-RTL`     | `MOD-RTL-FIFO`      | `async_fifo.v`                                |
| 测试平台        | `MOD-TB`      | `MOD-TB-FIFO`       | `tb_async_fifo.sv`                            |
| HLS IP          | `MOD-HLS`     | `MOD-HLS-ISP`       | `isp_pipeline.cpp`                            |
| AI 模型         | `MOD-AI`      | `MOD-AI-YOLOV8S`    | `yolov8s.yaml`                                |
| 任务（RTOS）    | `TASK`        | `TASK-SIG-FSM`      | `task_signal_fsm.c`                           |
| 测试用例        | `TC`          | `TC-FFT-001`        | `TC-FFT-001-impulse.md`                       |
| 测试计划        | `TP`          | `TP-FFT-001`        | `TP-FFT-001.md`                               |
| 测试报告        | `TR-REP`      | `TR-REP-2026-Q2`    | `TR-REP-2026-Q2.md`                           |
| 验证策略        | `VP`          | `VP-FFT-001`        | `VP-FFT-001.md`                               |
| 决策记录        | `ADR`         | `ADR-005`           | `ADR-005-async-clock.md`                      |
| 权衡研究        | `TR`          | `TR-002`            | `TR-002-pipeline-depth.md`                    |
| 问题            | `ISS`         | `ISS-042`           | `ISS-042-dpu-overtemp.md`                     |
| 概念/运行场景   | `CON-OP`      | `CON-OP-001`        | `CON-OP-001-daytime-rush.md`                  |

> **规则**：所有 ID 必须**全局唯一**；正则由 `tools/schemas/id-patterns.json` 给出并由校验脚本强制。

### 2.4 链接语法

#### Markdown 链接（人类可读）

```markdown
实现见 [MOD-C-FFT-32](core/04_IMPLEMENTATION/c/src/fft32.cpp)，
验证见 [TC-FFT-001](core/05_VERIFICATION/test-cases/TC-FFT-001-impulse.md)。
追溯需求：[SYS-REQ-012](core/01_REQUIREMENTS/system/SYS-REQ-012-latency.md)。
```

#### 代码内嵌标记（机器可读）

```cpp
// @req SYS-REQ-012, PERF-REQ-003
// @design DES-ARCH-007
// @test TC-FFT-001, TC-FFT-002
// @author zhang.san | @since 2026-04-10 | @version 1.2
// @status verified | @verified-at 2026-05-12
void fft32_process(...) { ... }
```

```verilog
// @req SYS-REQ-012
// @design DES-ARCH-007
// @test TC-RTL-FIFO-001
module async_fifo #(
    parameter WIDTH = 8,
    parameter DEPTH = 16
) (
    ...
);
```

```python
# @req SYS-REQ-013
# @design DES-ARCH-008
# @test TC-FFT-001
def byte_track_update(detections: list[Detection]) -> list[Track]:
    ...
```

#### YAML 结构化追溯

文件 `core/00_MANIFEST/traceability.yml`：

```yaml
- id: SYS-REQ-012
  title: "FFT 处理延迟 ≤ 10us"
  source: core/01_REQUIREMENTS/system/SYS-REQ-012-latency.md
  derived_from: [STK-REQ-001]
  design:
    - id: DES-ARCH-007
      source: core/02_ARCHITECTURE/decomposition/DES-ARCH-007-pipeline.md
  implementation:
    - id: MOD-C-FFT-32
      source: core/04_IMPLEMENTATION/c/src/fft32.cpp
    - id: MOD-RTL-FFT
      source: core/04_IMPLEMENTATION/verilog/rtl/fft_core.v
  verification:
    - id: TC-FFT-001
      source: core/05_VERIFICATION/test-cases/TC-FFT-001-impulse.md
    - id: TC-RTL-FFT-001
      source: core/05_VERIFICATION/test-cases/TC-RTL-FFT-001.md
  verification_method: simulation
  status: verified
  coverage: 100%
```

### 2.5 文档 front-matter 模板

每类文档的 front-matter 是**强制**的最小元数据；工具流据此分类、校验、索引。

```markdown
---
id: SYS-REQ-012                       # 唯一 ID
title: FFT 处理延迟 ≤ 10us              # 标题
type: requirement                      # requirement | design | interface | algorithm | test | adr | issue
status: draft                          # draft | reviewed | approved | verified | deprecated
owner: zhang.san                       # 主要负责人
version: 1.0
created: 2026-04-10
updated: 2026-05-12
priority: P0                           # P0 | P1 | P2 | P3
traces:
  up:    [STK-REQ-001]                 # 上游需求
  down:  [DES-ARCH-007, MOD-C-FFT-32, TC-FFT-001]   # 下游实现/验证
tags: [signal-processing, latency]
verification_method: simulation        # simulation | inspection | analysis | test
---

# SYS-REQ-012: FFT 处理延迟 ≤ 10us

## 描述
...

## 验收准则
1. 1024 点 FFT，端到端延迟 ≤ 10us
2. ...

## 变更历史
| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0  | 2026-04-10 | 张三 | 初始 |
```

### 2.6 状态机

所有带 `status` 字段的对象遵循统一状态机：

```
draft → reviewed → approved → verified → deprecated
            ↓           ↓
         rejected   deferred
```

| 状态       | 含义                          | 允许的转换目标                |
| ---------- | ----------------------------- | ----------------------------- |
| draft      | 初稿                          | reviewed, deprecated          |
| reviewed   | 已评审                        | approved, rejected, draft     |
| approved   | 已批准可实现                  | verified, deferred, draft     |
| verified   | 已通过验证                    | deprecated                    |
| rejected   | 评审不通过                    | draft, deprecated             |
| deferred   | 暂缓                          | approved, deprecated          |
| deprecated | 已废弃（不可用）              | -（终态）                     |

CI 门禁：**`approved` 之前不可在 `04_IMPLEMENTATION` 中被 `@req` 引用**；**`verified` 之前 release 阻断**。

---

## 3. 交叉互联脚本（核心部分的"血管"）

核心部分下设脚本目录 `tools/sw_hw_toolflow/core/`，由纯 Python（无 GUI 依赖）实现，作为
"活文档"的执行器；详见第 6 节工具流。下表给出与核心部分对应的脚本清单：

| 脚本                              | 功能                                              | 入口                 |
| --------------------------------- | ------------------------------------------------- | -------------------- |
| `core/build_index.py`             | 扫描 core/，生成 `00_MANIFEST/INDEX.md` + JSON    | pre-commit / 手动    |
| `core/validate_ids.py`            | 校验 ID 命名、唯一性、文件-内容一致性             | pre-commit           |
| `core/check_links.py`             | 校验 Markdown 链接、代码内 `@req/@design/@test`   | pre-commit / CI      |
| `core/build_traceability.py`      | 扫描标记，生成/更新 `traceability.yml`            | CI                   |
| `core/check_coverage.py`          | 检测未追溯需求/孤儿代码/未验证需求                | CI                   |
| `core/gen_diagrams.py`            | 编译 Mermaid/PlantUML → SVG/PNG                   | CI                   |
| `core/gen_docs.py`                | 从源码注释 + traceability 拼装 API/设计文档       | 手动 / 文档发布      |
| `core/lint_md.py`                 | Markdown 风格/lint                                | pre-commit           |
| `core/schema_validate.py`         | 校验所有 YAML/JSON 对应 schema                    | CI                   |
| `core/status_machine.py`          | 校验状态机转换合法性                              | CI                   |
| `core/pack_context.py`            | 把与某 ID 相关的文档/代码/测试打包为 LLM 上下文   | 手动 / Agent 任务    |
| `core/render_manifest.py`         | 重新生成 `00_MANIFEST/README.md` 导航             | 手动 / CI            |

所有脚本遵循同一接口规范：

```python
def main(core_root: Path, config: dict, args: argparse.Namespace) -> int:
    """返回 0=成功，非 0=失败，被 pre-commit/CI 调用。"""
```

---

## 4. 自动工具流（`tools/`，可迁移）

工具流是独立仓库 `sw-hw-toolflow`，通过 git submodule 引入。任何项目只要把
`configs/toolchain.yml` 改一下即可复用。

### 4.1 工具流目录

```
tools/                                # 独立仓库，可 git submodule add
├── pyproject.toml                    # 工具自身打包（Poetry/pip）
├── README.md                         # 工具流总览
├── sw_hw_toolflow/                   # 库代码
│   ├── __init__.py
│   ├── core/                         # 核心脚本（与 §3 一致）
│   │   ├── build_index.py
│   │   ├── validate_ids.py
│   │   ├── check_links.py
│   │   ├── build_traceability.py
│   │   ├── check_coverage.py
│   │   ├── gen_diagrams.py
│   │   ├── gen_docs.py
│   │   ├── lint_md.py
│   │   ├── schema_validate.py
│   │   ├── status_machine.py
│   │   ├── pack_context.py
│   │   ├── render_manifest.py
│   │   ├── project.py                # core/ 布局读写
│   │   ├── traceability.py           # traceability.yml 数据模型
│   │   └── ids.py                    # ID 解析/校验
│   ├── adapters/                     # 工具链适配器（与具体工具解耦）
│   │   ├── matlab_coder.py
│   │   ├── hdl_coder.py
│   │   ├── vivado.py
│   │   ├── modelsim.py
│   │   ├── verilator.py
│   │   ├── gcc.py
│   │   ├── cmake.py
│   │   ├── cocotb.py
│   │   ├── python.py
│   │   ├── petalinux.py
│   │   ├── openamp.py
│   │   ├── freertos.py
│   │   ├── pytorch.py
│   │   ├── vitis_ai.py
│   │   └── mqtt.py
│   ├── pipelines/                    # 端到端流水线
│   │   ├── algo_to_c.py              # 03_ALGORITHM/simulation → 04_IMPLEMENTATION/c
│   │   ├── algo_to_hdl.py            # 03_ALGORITHM/simulation → 04_IMPLEMENTATION/verilog
│   │   ├── c_sim_to_golden.py
│   │   ├── hdl_sim_to_golden.py
│   │   ├── c_rtl_co_sim.py
│   │   ├── hdl_coverage.py
│   │   ├── ai_quantize.py
│   │   ├── ai_deploy.py
│   │   ├── full_verify.py
│   │   ├── release.py
│   │   └── ota_build.py
│   ├── cli/                          # 命令行入口
│   │   ├── main.py
│   │   ├── verify.py
│   │   ├── trace.py
│   │   ├── build.py
│   │   ├── codegen.py
│   │   └── release.py
│   └── utils/
├── hooks/                            # Git hooks 模板
│   ├── pre-commit
│   ├── pre-push
│   └── commit-msg
├── make/                             # Makefile 片段
│   ├── toolflow.mk
│   ├── matlab.mk
│   ├── hdl.mk
│   ├── ai.mk
│   ├── rtos.mk
│   └── c.mk
├── schemas/                          # JSON Schema
│   ├── requirement.schema.json
│   ├── traceability.schema.json
│   ├── toolchain.schema.json
│   └── id-patterns.json
├── ci-templates/                     # CI 平台模板
│   ├── github-actions.yml
│   ├── gitlab-ci.yml
│   └── jenkins.Jenkinsfile
├── agents/                           # LLM Agent 模板
│   ├── requirements_writer.md
│   ├── design_reviewer.md
│   ├── test_generator.md
│   └── trace_fixer.md
└── tests/                            # 工具流自身测试
```

### 4.2 项目级工具链配置 `configs/toolchain.yml`

```yaml
project:
  name: edgevision-t1
  core_root: core

toolchains:
  matlab:
    enabled: true
    version: "R2023b"
    command: matlab
    license_server: 27000@licsrv

  matlab_coder:
    enabled: true
    target: C
    language_standard: c99
    optimization: speed

  hdl_coder:
    enabled: true
    target: verilog
    vendor: xilinx
    family: zynq-7000
    synthesis_tool: vivado

  hdl_sim:
    enabled: true
    simulator: verilator   # verilator | modelsim | vivado-xsim
    version: "5.020"

  c_build:
    enabled: true
    compiler: gcc
    standard: c11
    flags:
      debug:   ["-O0", "-g3", "-Wall", "-Wextra"]
      release: ["-O2", "-DNDEBUG"]
    coverage_tool: gcov

  ai:
    enabled: true
    framework: pytorch
    version: "2.1"
    quantizer: vitis_ai
    target: DPUCZDX8G          # ZCU102 DPU B4096

  fpga_synth:
    enabled: true
    tool: vivado
    version: "2023.2"
    top_module: ofdm_modem_top

  rtos:
    enabled: true
    rtos: freertos
    core: r5
    version: "10.4.0"

  ci:
    enabled: true
    runner: github
    matrix: [linux-x64, windows-x64]
    on_push:   [validate, build:c, sim:hdl]
    on_pr:     [full_verify]
```

### 4.3 端到端流水线示例

```bash
# 1. 代码生成（算法 → C / HDL）
sw-htf codegen algo-to-c  --src core/03_ALGORITHM/simulation/src/equalizer.py \
                          --out core/04_IMPLEMENTATION/c/src/equalizer.cpp

sw-htf codegen algo-to-hdl --src core/03_ALGORITHM/simulation/src/equalizer.py \
                           --out core/04_IMPLEMENTATION/verilog/rtl/equalizer.v

# 2. C 编译
sw-htf build c --config release

# 3. HDL 仿真 + 覆盖率
sw-htf sim hdl --test TC-RTL-FIFO-001 --coverage

# 4. C/RTL 协同仿真
sw-htf verify co-sim --c     core/04_IMPLEMENTATION/c/src/equalizer.cpp \
                      --rtl   core/04_IMPLEMENTATION/verilog/rtl/equalizer.v \
                      --vectors core/05_VERIFICATION/test-vectors/eq/

# 5. AI 量化 + 部署
sw-htf ai quantize --model core/04_IMPLEMENTATION/ai/models/yolov8s.yaml \
                   --out   core/04_IMPLEMENTATION/ai/quantization/

sw-htf ai deploy --quantized core/04_IMPLEMENTATION/ai/quantization/ \
                 --target    core/04_IMPLEMENTATION/ai/deploy/

# 6. 全链路验证
sw-htf verify full

# 7. 追溯检查
sw-htf trace check --strict
sw-htf trace matrix --out core/00_MANIFEST/traceability.yml

# 8. Release
sw-htf release build --version 2.3.1 --sign
sw-htf release ota --input builds/2.3.1 --output dist/edgevision-t1-2.3.1.swu
```

### 4.4 工具流 ↔ 核心部分的对应表

| 流水线阶段        | 核心部分输入                          | 核心部分输出                          | 触发条件                |
| ----------------- | ------------------------------------- | ------------------------------------- | ----------------------- |
| **需求变更**      | `01_REQUIREMENTS/*`                   | 更新 `traceability.yml`               | PR 修改 SYS-REQ         |
| **架构更新**      | `02_ARCHITECTURE/*`                   | 重新生成图/ICD                        | PR 修改 DES-ARCH        |
| **算法仿真**      | `03_ALGORITHM/simulation`             | `03_ALGORITHM/results`                | git push                |
| **黄金参考固化**  | `03_ALGORITHM/results`                | `03_ALGORITHM/golden-ref`             | 算法评审通过            |
| **代码生成**      | `03_ALGORITHM/simulation`             | `04_IMPLEMENTATION/{c,verilog,hls}`   | 算法变更                |
| **AI 训练/量化**  | `04_IMPLEMENTATION/ai/train`          | `04_IMPLEMENTATION/ai/deploy`         | 数据集更新              |
| **C 编译**        | `04_IMPLEMENTATION/c`                 | `04_IMPLEMENTATION/c/build`           | PR 修改 C 源码          |
| **HDL 综合/仿真** | `04_IMPLEMENTATION/verilog`           | `05_VERIFICATION/reports`             | PR 修改 RTL             |
| **RTOS 构建**     | `04_IMPLEMENTATION/rtos`              | `06_INTEGRATION/releases`             | PR 修改 R5 源码         |
| **功能验证**      | `05_VERIFICATION/*`                   | `05_VERIFICATION/reports`             | 手动/CI                 |
| **回归**          | `05_VERIFICATION/regressions`         | `06_INTEGRATION/releases`             | 每日/发版前             |
| **集成测试**      | `04_IMPLEMENTATION/*`                 | `05_VERIFICATION/integration`         | 手动                    |
| **部署**          | `06_INTEGRATION/deployment`           | 目标环境                              | tag 触发                |
| **反馈**          | `07_FEEDBACK/issues`                  | 新需求/ADR                            | 问题登记                |

---

## 5. 追溯与一致性保障

### 5.1 三层追溯

1. **文档层**：`front-matter.traces` 字段（人工维护初版）
2. **代码层**：`@req/@design/@test` 注释（开发者写）
3. **机器层**：`traceability.yml`（工具自动汇总 + 校验）

### 5.2 CI 检查矩阵

| 检查                   | 工具                          | 触发            | 失败处理       |
| ---------------------- | ----------------------------- | --------------- | -------------- |
| ID 唯一性              | `core/validate_ids.py`        | pre-commit      | 拒绝提交       |
| ID 命名格式            | `core/validate_ids.py`        | pre-commit      | 拒绝提交       |
| Markdown 链接          | `core/check_links.py`         | pre-commit      | 拒绝提交       |
| 代码注释标记解析       | `core/check_links.py`         | pre-commit / CI | 拒绝提交       |
| 需求覆盖率             | `core/check_coverage.py`      | CI              | 阻断 merge     |
| 孤儿代码（无 `@req`）  | `core/check_coverage.py`      | CI              | 警告/阻断     |
| 追溯矩阵与文档一致     | `core/build_traceability.py`  | CI              | 阻断 merge     |
| 黄金参考漂移           | `pipelines/c_rtl_co_sim.py`   | CI              | 阻断 release   |
| 状态机合法性           | `core/status_machine.py`      | CI              | 阻断 merge     |
| front-matter schema    | `core/schema_validate.py`     | CI              | 阻断 merge     |
| Markdown 风格          | `core/lint_md.py`             | pre-commit      | 警告           |
| 文档/代码同步          | `core/gen_docs.py --check`    | CI              | 警告           |

### 5.3 LLM/Agent 接入

- **入口**：`core/00_MANIFEST/INDEX.md` + `INDEX.json`
- **上下文构建脚本**：`core/pack_context.py` 把与某 ID 相关的文档/代码/测试打包为单一 prompt
- **Agent 模板**：`tools/agents/` 提供需求生成、设计评审、测试生成、追溯修复等子智能体
- **关键约束**：Agent 不会修改 `02_ARCHITECTURE/decomposition/*` 与 `04_IMPLEMENTATION/verilog/rtl/*` 之外的"大块"，避免意外越权

---

## 6. 跨项目迁移机制

| 维度         | 做法                                                                |
| ------------ | ------------------------------------------------------------------- |
| **核心部分** | 复制 `core/` 模板 + 修改 `00_MANIFEST/requirements.yml` 起步        |
| **工具流**   | `git submodule add <sw-hw-toolflow> tools` 或 `pip install sw-hw-toolflow` |
| **项目差异** | 仅改 `configs/toolchain.yml` 和 `core/00_MANIFEST/`                 |
| **CI 模板**  | `tools/ci-templates/{github,gitlab,jenkins}.yml` 直接引用           |
| **版本**     | `core/` 与 `tools/` 独立版本，工具流用 SemVer                       |

**新项目初始化**：

```bash
sw-htf init my-project --template edgevision-t1
cd my-project
git submodule add <sw-hw-toolflow> tools
# 修改 configs/toolchain.yml
# 编辑 core/00_MANIFEST/requirements.yml
sw-htf trace bootstrap   # 初始化 traceability.yml
```

---

## 7. 迭代与反馈闭环

1. **问题入口**：`core/07_FEEDBACK/issues/ISS-XXX.md`（问题用 Markdown 而非第三方系统）
2. **决策记录**：`core/07_FEEDBACK/adr/ADR-XXX.md`，链接到被影响的 SYS-REQ / DES-ARCH
3. **追溯回流**：每次 ADR 接受后，`build_traceability.py` 自动追加到 `traceability.yml` 的 `decisions` 段
4. **度量驱动**：`core/07_FEEDBACK/metrics/` 记录：
   - 需求稳定性 = 未变更需求 / 总需求
   - 需求覆盖率 = 已验证需求 / 已批准需求
   - 缺陷逃逸率 = 集成阶段发现 / 单元阶段发现
   - 黄金参考漂移次数
5. **复盘**：`core/07_FEEDBACK/retrospectives/` 每里程碑/迭代一份，反向推动 `02_ARCHITECTURE` 改进

---

## 8. 配置与文件规则

### 8.1 `.gitignore` 必备项

```gitignore
# 构建产物
core/04_IMPLEMENTATION/*/build/
core/04_IMPLEMENTATION/c/build/
core/04_IMPLEMENTATION/verilog/vivado_project/*.runs/
core/04_IMPLEMENTATION/verilog/vivado_project/*.cache/
core/04_IMPLEMENTATION/verilog/vivado_project/*.hw/
core/04_IMPLEMENTATION/verilog/vivado_project/*.sim/
core/04_IMPLEMENTATION/hls/*/solution*/.autopilot/
core/04_IMPLEMENTATION/ai/deploy/*.xmodel
core/04_IMPLEMENTATION/ai/quantization/*.pt
core/04_IMPLEMENTATION/ai/train/runs/

# 仿真中间
core/03_ALGORITHM/simulation/results/
core/03_ALGORITHM/simulation/figures/*.svg
core/05_VERIFICATION/reports/*.html
core/05_VERIFICATION/coverage/*.dat

# Vivado
.Xil/
*.jou
*.log
_xocc_*

# Python
__pycache__/
*.py[cod]

# LFS（指针保留）
*.xmodel filter=lfs diff=lfs merge=lfs -text
*.bit filter=lfs diff=lfs merge=lfs -text
*.elf filter=lfs diff=lfs merge=lfs -text
```

### 8.2 `.gitattributes`

```gitattributes
# 强制 LF
*.md         text eol=lf
*.yml        text eol=lf
*.yaml       text eol=lf
*.json       text eol=lf
*.tcl        text eol=lf
*.py         text eol=lf
*.cpp/.h/.c  text eol=lf
*.v/.sv      text eol=lf
*.proto      text eol=lf

# 二进制 LFS
*.xmodel filter=lfs diff=lfs merge=lfs -text
*.bit filter=lfs diff=lfs merge=lfs -text
*.elf filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
```

### 8.3 `configs/` 目录

| 文件                   | 作用                                          |
| ---------------------- | --------------------------------------------- |
| `toolchain.yml`        | 工具链映射（见 §4.2）                         |
| `project.yml`          | 项目元信息（名称、版本、维护者、仓库）        |
| `ci.yml`               | CI 平台选择、矩阵、定时任务                   |
| `release.yml`          | Release 流程（版本号、签名、OTA 通道）        |
| `secret.example.yml`   | 敏感配置模板（实际值不入库，CI secret 注入）  |

---

## 9. 关键设计取舍

1. **Markdown + YAML 而非数据库**：纯文本 → git diff、LLM 直接吃；性能换可读性（万级文档以内可接受）
2. **ID 前缀强约束**：工具流可在 ms 级校验完所有 ID，正则驱动即可
3. **代码内嵌 `@req` 而非外部映射表**：写代码时即完成追溯，避免"实现后忘记登记"
4. **核心/工具解耦为子模块**：工具流可独立升级、复用、回滚
5. **黄金参考固化在 `golden-ref/` 而非测试向量**：算法层和实现层使用同一基准，bug 一旦让黄金参考漂移必须走 ADR
6. **CI 中的需求覆盖率门禁**：强制"先批准后实现、先验证后合并"，避免文档与代码脱节
7. **状态机集中于 front-matter**：把"被评审/已批准/已验证"显性化，工具流可据此阻断非法合并
8. **bindings 目录**：Web UI、Python SDK、CLI 客户端等都视为"语言绑定"，与核心算法/协议解耦

---

## 10. 实施路线

| 阶段       | 1 周     | 2 周     | 1 月      | 2 月      |
| ---------- | -------- | -------- | --------- | --------- |
| 骨架       | 建 `core/` 目录、ID 规范、front-matter 模板 | 接入 GitHub/GitLab CI、pre-commit | — | — |
| 追溯       | 写 3 个示例需求 + 设计 + 实现 + 测试 + traceability | `check_links` / `check_coverage` 上 CI | — | — |
| 工具流     | 子模块引入 sw-hw-toolflow | 接入 MATLAB Coder / HDL Coder / Vitis AI 适配器 | — | — |
| 验证       | —        | 写第一个 C→RTL 协同仿真流水线 | 覆盖率 + 黄金参考 | 全链路 `full_verify` |
| Agent      | —        | —        | `pack_context` + 需求/测试生成 Agent | 接入设计/代码评审 Agent |

---

## 11. 参考

- 项目自带的 `core/00_MANIFEST/INDEX.md`（自动生成）
- 项目自带的 `core/00_MANIFEST/traceability.yml`（自动生成）
- `tools/README.md`（工具流总览）
- 顶层 `README.md`（项目入口导航）
