# EdgeVision-T1 智能交通路口感知终端

> 基于 Xilinx ZCU102（Zynq UltraScale+ MPSoC）的商业级参考案例  
> 覆盖深度学习推理 / 高速视频传输 / 实时控制 / 云边协同全栈开发  
> **本仓库即"高可靠、可追溯、可扩展"软硬件协同开发文件组织架构的实施示例**

---

## ⚡ 30 秒上手

```bash
# 1. 查看架构宪法（必读）
cat ARCHITECTURE.md

# 2. 查看项目入口
cat core/00_MANIFEST/README.md

# 3. 查看文档全索引
cat core/00_MANIFEST/INDEX.md

# 4. 跑闭环仿真（无硬件依赖）
python3 core/03_ALGORITHM/simulation/src/traffic_sim.py --frames 600

# 5. 跑端到端集成测试
python3 core/05_VERIFICATION/integration/e2e_integration.py -v

# 6. 工厂功能测试（针对实机）
python3 core/06_INTEGRATION/ci-cd/factory_test.py <device_ip> <device_id>
```

---

## 📐 架构总览

本仓库是 [ARCHITECTURE.md](ARCHITECTURE.md) 描述的**软硬件协同开发文件组织架构**的完整落地实例。

```
┌────────────────────────────────────────────────────────────────────┐
│                       项目仓库（本仓库）                            │
│                                                                     │
│  ARCHITECTURE.md       架构宪法（11 章，权威）                      │
│  README.md             本文件                                       │
│                                                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐  │
│  │   core/  核心部分         │  │  tools/  工具流              │  │
│  │   纯文本、git 友好        │  │  可迁移、配置驱动              │  │
│  │                          │  │                              │  │
│  │   00_MANIFEST/   入口    │  │  sw_hw_toolflow/             │  │
│  │   01_REQUIREMENTS/ 需求 │  │   ├─ core/    追溯/校验      │  │
│  │   02_ARCHITECTURE/ 架构 │  │   ├─ adapters  工具链适配    │  │
│  │   03_ALGORITHM/    算法 │  │   ├─ pipelines 端到端流水线  │  │
│  │   04_IMPLEMENTATION/实现│  │   └─ cli/      命令行入口    │  │
│  │   05_VERIFICATION/ 验证 │  │  hooks/      Git hooks       │  │
│  │   06_INTEGRATION/  集成 │  │  schemas/    JSON Schema     │  │
│  │   07_FEEDBACK/    反馈  │  │  ci-templates/  CI 模板      │  │
│  │   99_REFERENCES/  参考  │  │                              │  │
│  └──────────────────────────┘  └──────────────────────────────┘  │
│                          ▲                                          │
│                          │  configs/  项目级配置（工具链映射）       │
│                          │   - toolchain.yml                         │
│                          │   - project.yml                           │
│                          │   - ci.yml                                │
│                          │   - release.yml                           │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📚 关键文档入口

| 入口                                          | 用途                                       |
| --------------------------------------------- | ------------------------------------------ |
| **[ARCHITECTURE.md](ARCHITECTURE.md)**         | 架构宪法（11 章，权威，必读）              |
| **[core/00_MANIFEST/README.md](core/00_MANIFEST/README.md)** | 项目入口、导航、关键指标        |
| [core/00_MANIFEST/INDEX.md](core/00_MANIFEST/INDEX.md) | 文档全索引（自动生成）           |
| [core/00_MANIFEST/requirements.yml](core/00_MANIFEST/requirements.yml) | 需求库（结构化）          |
| [core/00_MANIFEST/traceability.yml](core/00_MANIFEST/traceability.yml) | 追溯矩阵（结构化）         |
| [core/00_MANIFEST/glossary.md](core/00_MANIFEST/glossary.md)     | 术语表                       |
| [core/00_MANIFEST/metrics.yml](core/00_MANIFEST/metrics.yml)     | 项目度量                     |
| [core/00_MANIFEST/decisions.log](core/00_MANIFEST/decisions.log) | 决策日志                     |
| [configs/toolchain.yml](configs/toolchain.yml)   | 工具链映射（v1.0 全量）         |
| [tools/README.md](tools/README.md)              | 工具流总览                     |

---

## 🎯 项目一句话

**EdgeVision-T1** 是一台部署在城市路口的多模态边缘感知盒，可接入 4 路 4K 摄像头，在
FPGA 加速下完成实时车辆/行人检测、车牌识别、流量统计与违规事件上报，并通过
10GbE/CAN 分别对接城市云平台与信号灯控制器。

## ✅ 核心指标

| 指标              | 目标     | 实测     | 状态 |
| ----------------- | -------- | -------- | ---- |
| 4K 摄像头接入     | 4 路 30fps | 4 路 30fps | ✔   |
| 检测 mAP50        | ≥ 85%   | 88.5%    | ✔   |
| 车牌准确率        | ≥ 95%   | 95.3%    | ✔   |
| 跟踪 MOTA         | ≥ 75%   | 76.2%    | ✔   |
| 端到端延迟        | < 30ms  | 22ms     | ✔   |
| CAN 指令延迟      | < 10ms  | 5ms      | ✔   |
| 云端事件延迟      | < 500ms | 198ms    | ✔   |
| 24h 离线补传      | 100%    | 100%     | ✔   |
| 整机功耗          | < 35W   | 28W      | ✔   |
| 启动时间          | < 15s   | 12s      | ✔   |

详细指标：[metrics.yml](core/00_MANIFEST/metrics.yml)、[TR-REP-2026-Q2](core/05_VERIFICATION/reports/TR-REP-2026-Q2.md)

---

## 🏗️ 硬件平台

- **MPSoC**：Xilinx Zynq UltraScale+ XCZU9EG-2FFVB1156E
  - PL：~274K LUT / 548K FF / 912 BRAM / 2520 DSP
  - PS：A53 (Linux) + R5 (FreeRTOS)
- **DDR4 4GB**
- **eMMC 32GB**
- **接口**：
  - 4× MIPI CSI-2 4-lane（4K 摄像头）
  - 1× USB3.0（备用 UVC）
  - 1× 10GbE SFP+
  - 1× DisplayPort 1.2
  - 1× CAN 2.0B
  - 1× GPS PPS

## 💻 软件栈

| 层 | 技术 |
|----|------|
| AI | YOLOv8s INT8 + LPRNet INT8 (DPU B4096) |
| 跟踪 | ByteTrack (Python 仿真 / C++ 部署) |
| 视频 | Vitis HLS ISP + OSD |
| OS | PetaLinux 2023.1 + FreeRTOS 10.4.0 |
| 通信 | MQTT (EMQX) + gRPC + OpenAMP RPMsg |
| 升级 | SWUpdate A/B 分区 |
| Web | Vue 3 + Vite |
| 仿真 | Python (OpenCV) |

---

## 🚀 快速运行

### 闭环仿真（推荐，无硬件依赖）

```bash
python3 core/03_ALGORITHM/simulation/src/traffic_sim.py --frames 600 --seed 42
```

预期输出：
- 30+ fps 仿真速度
- 闯红灯、逆行、违规停车、行人闯红灯 4 类事件
- 信号灯 6 步相位自动切换

### 集成测试

```bash
python3 core/05_VERIFICATION/integration/e2e_integration.py -v
```

7 个子用例，覆盖：场景生成、检测、跟踪、事件检测、信号灯、完整管道、可复现性。

### 工厂量产测试（实机）

```bash
python3 core/06_INTEGRATION/ci-cd/factory_test.py 192.168.1.100 edge001
```

需要 SSH 访问设备。

### 完整构建（需要 Vivado/PetaLinux/Vitis AI 环境）

```bash
bash core/06_INTEGRATION/ci-cd/build_all.sh
```

产物：`BOOT.BIN`, `image.ub`, `rootfs.tar.gz` 等。

---

## 📦 仓库结构

```
案例-智能交通路口感知平台/
├── ARCHITECTURE.md                  架构宪法
├── README.md                        本文件
├── .gitignore
├── .gitattributes
│
├── core/                            核心部分（纯文本）
│   ├── 00_MANIFEST/                 入口与元数据
│   ├── 01_REQUIREMENTS/             需求（35+ 文档）
│   ├── 02_ARCHITECTURE/             架构（4+1 视图、分解、ICD、TR）
│   ├── 03_ALGORITHM/                算法（理论、仿真、黄金参考）
│   ├── 04_IMPLEMENTATION/           实现（C/C++/HLS/Verilog/RTOS/AI/Proto/Web）
│   ├── 05_VERIFICATION/             验证（计划、用例、报告、集成）
│   ├── 06_INTEGRATION/              集成（CI/CD、部署、Release）
│   ├── 07_FEEDBACK/                 反馈（问题、ADR、复盘）
│   └── 99_REFERENCES/               参考 + 历史 docs/
│
├── tools/                           工具流（可迁移）
│   ├── sw_hw_toolflow/              Python 库
│   ├── hooks/                       Git hooks 模板
│   ├── schemas/                     JSON Schema
│   ├── ci-templates/                CI 平台模板
│   └── ...
│
└── configs/                         项目配置
    ├── toolchain.yml                工具链映射
    ├── project.yml                  项目元信息
    ├── ci.yml                       CI 平台
    ├── release.yml                  Release 流程
    └── secret.example.yml           敏感配置模板
```

---

## 🧭 角色导航

| 你是 | 请阅读 |
|------|--------|
| 项目经理 | [README.md](README.md) · [metrics.yml](core/00_MANIFEST/metrics.yml) · [decisions.log](core/00_MANIFEST/decisions.log) |
| 架构师 | [ARCHITECTURE.md](ARCHITECTURE.md) · [02_ARCHITECTURE/](core/02_ARCHITECTURE/) · [07_FEEDBACK/adr/](core/07_FEEDBACK/adr/) |
| FPGA 工程师 | [04_IMPLEMENTATION/hls/](core/04_IMPLEMENTATION/hls/) · [04_IMPLEMENTATION/verilog/](core/04_IMPLEMENTATION/verilog/) |
| 嵌入式工程师 | [04_IMPLEMENTATION/c/](core/04_IMPLEMENTATION/c/) · [04_IMPLEMENTATION/rtos/](core/04_IMPLEMENTATION/rtos/) |
| AI 工程师 | [04_IMPLEMENTATION/ai/](core/04_IMPLEMENTATION/ai/) · [03_ALGORITHM/theory/](core/03_ALGORITHM/theory/) |
| 算法仿真 | [03_ALGORITHM/simulation/](core/03_ALGORITHM/simulation/) |
| 测试工程师 | [05_VERIFICATION/](core/05_VERIFICATION/) · [06_INTEGRATION/ci-cd/](core/06_INTEGRATION/ci-cd/) |
| LLM/Agent | [core/00_MANIFEST/INDEX.md](core/00_MANIFEST/INDEX.md) · [core/pack_context.py](core/_meta/scripts/pack_context.py) |
| 工具流开发者 | [tools/README.md](tools/README.md) · [ARCHITECTURE.md §4](ARCHITECTURE.md) |

---

## 📋 状态

| 段 | 状态 |
|----|------|
| 0. 入口 | ✔ 完成 |
| 1. 需求 | ✔ 35+ 文档 |
| 2. 架构 | ✔ 4+1 视图、10 分解、6 ICD、3 TR |
| 3. 算法 | ✔ 仿真、黄金参考、2 理论 |
| 4. 实现 | ✔ C/HLS/Verilog/RTOS/AI/Proto/Web |
| 5. 验证 | ✔ 11 测试用例 + 集成 + 报告 |
| 6. 集成 | ✔ 6 脚本 + OTA + 工厂 |
| 7. 反馈 | ✔ 3 ADR + 模板 |
| 9. 参考 | ✔ 8 旧 docs 已迁移 |
| 工具流 | ✔ 骨架 + pre-commit + schema |
| 配置 | ✔ 5 yml 完整 |
| ARCHITECTURE.md | ✔ 11 章完整 |

---

## 📄 许可证

Apache-2.0

## 🤝 贡献

1. 阅读 [ARCHITECTURE.md](ARCHITECTURE.md)
2. Fork → feature/your-feature
3. `sw-htf trace check --strict` 通过
4. CI 全绿
5. PR 评审
6. 合并

---

> **本仓库即规范本身**。任何对目录结构、ID 命名、追溯约定、工具流的修改，**先写 ADR**。
