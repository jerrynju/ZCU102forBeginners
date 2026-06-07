# ZCU102 开发板资源索引

> 自动搜集于 2026-06-03 | Xilinx Zynq UltraScale+ MPSoC ZCU102 Evaluation Kit

## 1. 官方文档

| 文档 | 编号 | 说明 |
|------|------|------|
| Evaluation Board User Guide | UG1182 (v1.6) | 完整硬件参考，含引脚定义、接口说明、启动配置 |
| Quick Start Guide | XTP426 | 快速入门指南 |
| Schematics | XTP454 | 原理图 |
| Board Interface Test | XTP428 | 板卡接口测试 |
| Restoring Flash Contents | XTP434 | Flash 恢复 |
| System Controller GUI Tutorial | XTP433 | 系统控制器教程 |
| MIG Design Creation | XTP432 | DDR 内存接口设计 |
| IP Integrator Application | XTP431 | IP 集成器应用 |
| GTH IBERT Design Creation | XTP430 | GTH 收发器 IBERT 设计 |
| Software Install & Board Setup | XTP435 | 软件安装与板卡设置 |

## 2. 参考设计 (TRD)

| 设计 | 版本 | 说明 |
|------|------|------|
| Base TRD | 2021.1 | Zynq UltraScale+ MPSoC 基础参考设计 |
| Software Acceleration TRD | 2018.3 | 软件加速参考设计 |
| Vitis Base Platform | 2024.1 | Vitis 嵌入式基础平台 |

## 3. 板卡设计文件

| 文件 | 说明 |
|------|------|
| zcu102-schematic-source-rdf0403.zip | 原理图源文件 |
| zcu102-bom-rdf0404.zip | BOM 物料清单 |
| zcu102-xdc-rdf0405.zip | XDC 约束文件 |
| zcu102-allegro-board-source-rdf0406.zip | Allegro 板卡源文件 |
| zcu102-gerber-files-rdf0407.zip | Gerber 文件 |

## 4. 关键参数

- **芯片**: XCZU9EG-2FFVB1156E (Zynq UltraScale+ MPSoC)
- **PS**: Quad-core ARM Cortex-A53 + Dual-core ARM Cortex-R5
- **PL**: 600K System Logic Cells, 2520 DSP Slices
- **内存**: 4GB DDR4 (PS) + 512MB DDR4 (PL)
- **连接**: SFP+, FMC HPC, HDMI, DisplayPort, USB3.0, GbE, PCIe Gen2 x4
- **存储**: SD Card, QSPI Flash, SATA

## 5. 官方链接

- 产品页: https://www.xilinx.com/products/boards-and-kits/ek-u1-zcu102-g.html
- 文档门户: https://docs.amd.com/v/u/en-US/ug1182-zcu102-eval-bd
- 已知问题: AR66752 - ZCU102 Known Issues and Release Notes
- 支持中心: AR43745 - AMD Boards and Kits Solution Center
- Vitis 平台: https://github.com/Xilinx/xilinx-zcu102-v2024.1

## 6. 目录结构

```
zcu102/
├── docs/           # 文档 (UG1182, 原理图, 快速入门等)
├── projects/       # 工程项目 (Vitis 平台, Vitis AI 教程等)
└── README.md       # 本索引文件
```
