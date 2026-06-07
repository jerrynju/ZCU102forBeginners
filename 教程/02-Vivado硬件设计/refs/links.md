# 阶段 2 参考资源链接

## 核心官方教程

### 1. Vivado IP Integrator 教程
- **仓库**: https://github.com/Xilinx/Vivado-Design-Tutorials
- **关键路径**:
  - `General/IP_Integrator/Designing_in_IPI/` — Block Design 基础（MicroBlaze/Zynq 方法论相同）
  - `General/IP_Integrator/BlockDesignContainers_in_IPI/` — 层次化设计
  - `General/IP_Integrator/ModuleReferencing_in_IPI/` — RTL 模块集成
  - `General/Revision_Control/Foundational/` — Tcl 版本控制（必学）
  - `UltraScalePlus/DFX/DFX_Decoupler/` — 动态局部重构（针对 Zynq UltraScale+）

### 2. ZCU102 嵌入式设计教程 Chapter 3
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: `docs/Getting_Started/ZynqMPSoC-EDT/3-system-configuration.rst`
- **内容**: ZCU102 Vivado Block Design 创建、PS IP 配置（DDR/UART/ETH）、XSA 导出

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| UG994 | Vivado Design Suite: Designing IP Subsystems Using IP Integrator | IPI 完整手册 |
| UG1085 | Zynq UltraScale+ TRM, Chapter 3 | PS-PL 接口（AXI HP/HPC/GP/ACE）|
| UG899 | Vivado Design Suite: I/O and Clock Planning | 引脚约束和时钟规划 |
| UG908 | Vivado Design Suite: Programming and Debugging | 约束文件格式 |
| PG021 | AXI DMA Product Guide | AXI DMA IP |
| PG144 | AXI GPIO Product Guide | AXI GPIO IP |
| PG082 | AXI Interconnect Product Guide | AXI 互连 IP |
| PG059 | AXI BRAM Controller Product Guide | BRAM 控制器 |

## ZCU102 引脚参考
- **原理图**: UG1182 附录 A（LED/开关/按键引脚分配）
- **Master XDC**: https://www.xilinx.com/member/forms/download/design-license.html?cid=1900148
  - 包含 ZCU102 所有板载资源的 XDC 约束模板
