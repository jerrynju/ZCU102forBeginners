---
id: PROJ-EDGEVISION-T1
title: EdgeVision-T1 智能路口感知终端
type: project-manifest
status: active
owner: architect-team
version: 1.0.0
created: 2026-06-04
updated: 2026-06-04
---

# EdgeVision-T1 智能路口感知终端

> 基于 Xilinx ZCU102（Zynq UltraScale+ MPSoC）的商业级参考案例  
> 覆盖深度学习推理 / 高速视频传输 / 实时控制 / 云边协同全栈开发  
> 适用本仓库的"高可靠、可追溯、可扩展"软硬件协同开发文件组织架构

---

## 1. 项目一句话

**EdgeVision-T1** 是一台部署在城市路口的多模态边缘感知盒，可接入 4 路 4K 摄像头，在
FPGA 加速下完成实时车辆/行人检测、车牌识别、流量统计与违规事件上报，并通过
10GbE/CAN 分别对接城市云平台与信号灯控制器。

---

## 2. 仓库入口

| 入口                                          | 用途                                |
| --------------------------------------------- | ----------------------------------- |
| [ARCHITECTURE.md](../../ARCHITECTURE.md)      | **架构宪法**，必读                 |
| [README.md](../../README.md)                  | 项目总览与快速开始                  |
| [core/00_MANIFEST/INDEX.md](INDEX.md)         | 文档全索引（自动生成）              |
| [core/00_MANIFEST/requirements.yml](requirements.yml) | 需求库（结构化）            |
| [core/00_MANIFEST/traceability.yml](traceability.yml) | 追溯矩阵（结构化）            |
| [configs/toolchain.yml](../../configs/toolchain.yml)   | 工具链映射                  |
| [tools/README.md](../../tools/README.md)      | 工具流使用说明                      |

---

## 3. 核心部分目录（7 段流水线）

| 段            | 路径                | 内容                                             |
| ------------- | ------------------- | ------------------------------------------------ |
| 0. 入口       | `00_MANIFEST/`      | 项目元数据、INDEX、追溯矩阵、术语表             |
| 1. 需求       | `01_REQUIREMENTS/`  | 干系人/系统/接口/性能/安全/法规/验证             |
| 2. 架构       | `02_ARCHITECTURE/`  | 4+1 视图、模块分解、ICD、权衡研究               |
| 3. 算法       | `03_ALGORITHM/`     | 数学理论、仿真、黄金参考、度量                   |
| 4. 实现       | `04_IMPLEMENTATION/`| C/C++/HLS/Verilog/RTOS/AI 模型/Web 绑定        |
| 5. 验证       | `05_VERIFICATION/`  | 测试计划/用例/向量/平台/报告/覆盖率/回归/集成   |
| 6. 集成       | `06_INTEGRATION/`   | CI/CD、环境、Release、部署                       |
| 7. 反馈       | `07_FEEDBACK/`      | 问题、ADR、评审、度量、复盘                      |
| 9. 参考       | `99_REFERENCES/`    | 论文、标准、数据手册、历史文档                   |

---

## 4. 工具流

工具流位于仓库根 `tools/`，可作为独立仓库 `sw-hw-toolflow` 的子模块引入。
通过 `configs/toolchain.yml` 与本项目适配。

主要命令：

```bash
sw-htf trace check          # 追溯校验
sw-htf verify full          # 全链路验证
sw-htf build c              # C 编译
sw-htf sim hdl              # HDL 仿真
sw-htf ai quantize          # AI 量化
sw-htf release build        # 发布构建
```

详见 [tools/README.md](../../tools/README.md)。

---

## 5. 干系人

| 角色               | 关注点                        |
| ------------------ | ----------------------------- |
| 城市交通管理局     | 数据合规、可靠性、运维 SLA    |
| 集成商/渠道商      | 集成便利性、二次开发能力      |
| 终端运维人员       | 远程管理、故障诊断、OTA       |
| 算法团队           | 模型迭代速度、回滚能力        |
| 硬件团队           | 时序收敛、量产良率            |

详见 [stakeholders.md](stakeholders.md)。

---

## 6. 术语

详见 [glossary.md](glossary.md)。

---

## 7. 状态总览

| 指标                | 当前值 | 目标     |
| ------------------- | ------ | -------- |
| 已批准需求          | 6      | 全部     |
| 已实现需求          | 6      | 全部     |
| 已验证需求          | 4      | ≥ 95%   |
| 黄金参考漂移（30d） | 0      | 0        |
| 开放问题            | 0      | ≤ 5      |
| ADR 累计            | 0      | 持续增长 |

详见 [metrics.yml](metrics.yml)。
