# ZCU102 开发板入门资源库

> Xilinx Zynq UltraScale+ MPSoC ZCU102 Evaluation Kit — 面向初学者的完整学习资源

---

## 快速了解 ZCU102

| 类别 | 参数 |
|------|------|
| 芯片 | XCZU9EG-2FFVB1156E (Zynq UltraScale+ MPSoC) |
| PS 处理器 | Quad ARM Cortex-A53 (1.5GHz) + Dual ARM Cortex-R5 (600MHz) |
| PL 逻辑 | 600K System Logic Cells · 2520 DSP Slices · 32.1Mb BRAM |
| DDR4 (PS) | 4GB，64-bit ECC |
| DDR4 (PL) | 512MB |
| 主要接口 | SFP+、FMC HPC、HDMI 2.0、DisplayPort、USB3.0、GbE、PCIe Gen2 x4 |
| 存储 | SD Card、QSPI Flash (512Mb)、SATA M.2 |

---

## 目录结构

```
ZCU102forBeginners/
├── 教程/                          # 分阶段学习教程（10章）
│   ├── 01-环境搭建与工具链/
│   ├── 02-Vivado硬件设计/
│   ├── 03-Vitis嵌入式软件/
│   ├── 04-PetaLinux与设备驱动/
│   ├── 05-Vitis-HLS高层次综合/
│   ├── 06-AI推理与Vitis-AI/
│   ├── 07-高速接口与串行协议/
│   ├── 08-RTOS与多核异构/
│   ├── 09-系统集成与调试/
│   └── 10-商业项目实战/
├── 学习资源/                      # 商业化开发各阶段学习资料（9章）
│   ├── 01-需求分析与可行性评估/
│   ├── 02-系统架构设计/
│   ├── 03-FPGA_PL硬件逻辑开发/
│   ├── 04-嵌入式软件开发/
│   ├── 05-系统集成与验证/
│   ├── 06-定制硬件板卡设计/
│   ├── 07-认证与合规/
│   ├── 08-量产与制造/
│   └── 09-商业运营与全生命周期管理/
├── 案例-智能交通路口感知平台/     # 完整商业闭环案例
│   ├── core/                      # 需求→架构→算法→实现→验证→集成→反馈
│   ├── configs/                   # 项目配置文件
│   └── tools/                     # CI 模板与工具链
├── 参考资料/                      # 官方手册与学习文档
│   ├── 官方手册/                  # AMD/Xilinx 官方 PDF 文档
│   ├── 学习指南/                  # DPU TRD 等专题学习指南
│   ├── 在线资源导航/              # 学习资源导航网页
│   └── ZCU102商业闭环开发流程.md # 商业产品全流程概述
└── projects/                      # 参考项目（git submodule）
    ├── zcu102-vitis-platform/     # Xilinx Vitis 嵌入式平台源码 (2024.1)
    ├── zcu102-dpu-trd/            # Xilinx Vitis AI DPU TRD
    ├── vitis-ai-zcu102-tutorial/  # Vitis AI 教程 (MNIST/CIFAR-10)
    ├── zcu102-pynq/               # PYNQ Python 开发框架
    └── zcu102-petalinux-bsp/      # 嵌入式软件 BSP
```

---

## 官方文档

| 文档 | 编号 | 说明 |
|------|------|------|
| [User Guide](参考资料/官方手册/UG1182_ZCU102_User_Guide.pdf) | UG1182 (v1.6) | 完整硬件参考，含引脚定义、接口说明、启动配置 |
| [Quick Start Guide](参考资料/官方手册/XTP426_ZCU102_QuickStart.pdf) | XTP426 | 快速入门，含 BIST 自检与工具安装 |
| [Base TRD Guide](参考资料/官方手册/UG1221_ZCU102_Base_TRD.pdf) | UG1221 | ZCU102 基础参考设计用户指南 |
| Schematics | XTP454 | 原理图（需从 AMD 官网手动下载） |
| XDC Constraints | rdf0405 | FPGA 引脚约束（需手动下载） |

---

## 参考设计

| 项目 | 来源 | 说明 |
|------|------|------|
| `zcu102-vitis-platform` | Xilinx/Vitis_Embedded_Platform_Source | Vitis 嵌入式平台 (2024.1) |
| `zcu102-dpu-trd` | Xilinx/Vitis-AI | Vitis AI DPU 参考设计，含模型库与 Docker 环境 |
| `vitis-ai-zcu102-tutorial` | al3monni | Vitis AI 3.5 + TF2.16 教程 (MNIST/CIFAR-10) |
| `zcu102-pynq` | Xilinx/PYNQ | PYNQ Jupyter 开发框架 |
| `zcu102-petalinux-bsp` | Xilinx/embeddedsw | 嵌入式软件 BSP（裸机/FreeRTOS/Linux 驱动） |

> 初次克隆后执行 `git submodule update --init --recursive` 下载子模块内容。

---

## 官方链接

- 产品主页：https://www.xilinx.com/products/boards-and-kits/ek-u1-zcu102-g.html
- 在线文档：https://docs.amd.com/v/u/en-US/ug1182-zcu102-eval-bd
- Vitis 平台：https://github.com/Xilinx/Vitis_Embedded_Platform_Source
- 已知问题：AR66752 - ZCU102 Known Issues and Release Notes
- 支持中心：https://adaptivesupport.amd.com
