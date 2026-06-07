# ZCU102 分阶段学习指南

> 面向 Xilinx ZCU102（xczu9eg-ffvb1156-2-e）的系统性 FPGA 全栈开发教程。
> 对应工具链：Vivado 2023.1 / Vitis 2023.1 / PetaLinux 2023.1 / Vitis AI 3.5

---

## 学习路径总览

```
阶段 1  环境搭建与工具链        → Vivado/Vitis/PetaLinux 安装、License、板卡验证
阶段 2  Vivado 硬件设计         → Block Design、DMA、中断、时序约束
阶段 3  Vitis 嵌入式软件        → Standalone/FreeRTOS Baremetal、驱动调用、调试
阶段 4  PetaLinux 与设备驱动    → Yocto 构建、DT、自定义内核驱动、rootfs
阶段 5  Vitis HLS 高层次综合    → C/C++ → RTL、指令优化、AXI 接口生成
阶段 6  AI 推理与 Vitis AI      → YOLOv8 量化、DPU 部署、VART 推理框架
阶段 7  高速接口与串行协议      → GTH 10GbE、MIPI CSI-2、AXI CAN、PCIe
阶段 8  RTOS 与多核异构         → FreeRTOS R5、OpenAMP RPMsg、A53+R5 协同
阶段 9  系统集成与调试          → ILA/VIO、ChipScope、性能分析、OTA
阶段 10 商业项目实战            → 智能交通路口感知平台端到端复现
```

---

## 各阶段目录说明

| 目录 | 内容 | 预计时间 |
|------|------|----------|
| [01-环境搭建与工具链](01-环境搭建与工具链/README.md) | 工具安装、License、板卡上电验证 | 1-2天 |
| [02-Vivado硬件设计](02-Vivado硬件设计/README.md) | Block Design、PS配置、AXI外设 | 3-5天 |
| [03-Vitis嵌入式软件](03-Vitis嵌入式软件/README.md) | Standalone/RTOS、驱动、调试 | 3-5天 |
| [04-PetaLinux与设备驱动](04-PetaLinux与设备驱动/README.md) | Linux构建、DT Overlay、字符驱动 | 5-7天 |
| [05-Vitis-HLS高层次综合](05-Vitis-HLS高层次综合/README.md) | HLS C综合、指令、AXI接口 | 3-5天 |
| [06-AI推理与Vitis-AI](06-AI推理与Vitis-AI/README.md) | DPU配置、PTQ量化、VART部署 | 5-7天 |
| [07-高速接口与串行协议](07-高速接口与串行协议/README.md) | GTH、MIPI、CAN、PCIe | 5-7天 |
| [08-RTOS与多核异构](08-RTOS与多核异构/README.md) | FreeRTOS、OpenAMP、IPC | 3-5天 |
| [09-系统集成与调试](09-系统集成与调试/README.md) | ILA、VIO、性能优化、OTA | 3-4天 |
| [10-商业项目实战](10-商业项目实战/README.md) | 端到端智能交通项目复现 | 7-14天 |

---

## 参考资源索引

所有教程均对应 Xilinx 官方资源，详见各阶段 `refs/` 子目录：

- **Vivado 教程**: [github.com/Xilinx/Vivado-Design-Tutorials](https://github.com/Xilinx/Vivado-Design-Tutorials)
- **Vitis 教程**: [github.com/Xilinx/Vitis-Tutorials](https://github.com/Xilinx/Vitis-Tutorials)
- **Vitis AI 教程**: [github.com/Xilinx/Vitis-AI](https://github.com/Xilinx/Vitis-AI)
- **嵌入式软件库**: [github.com/Xilinx/embeddedsw](https://github.com/Xilinx/embeddedsw)
- **ZCU102 板卡文件**: [github.com/Xilinx/XilinxBoardStore](https://github.com/Xilinx/XilinxBoardStore)

---

## 硬件要求

| 组件 | 规格 |
|------|------|
| 开发板 | Xilinx ZCU102 Evaluation Kit (xczu9eg-ffvb1156-2-e) |
| 主机 OS | Ubuntu 20.04 / 22.04 LTS (x86_64) |
| 内存 | ≥ 32 GB RAM（Vivado 综合推荐 ≥ 64 GB） |
| 存储 | ≥ 200 GB SSD（工具链 + 项目） |
| 工具版本 | Vivado 2023.1 / Vitis 2023.1 / PetaLinux 2023.1 |

---

## 快速验证（无额外硬件）

已有闭环仿真层，无需 FPGA 比特流即可验证核心逻辑：

```bash
cd ../案例-智能交通路口感知平台
sudo bash scripts/setup_sim_env.sh
python3 tests/e2e_integration.py -v
```
