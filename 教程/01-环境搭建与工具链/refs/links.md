# 阶段 1 参考资源链接

## 核心官方教程

### 1. Zynq MPSoC 嵌入式设计教程（最重要）
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: `docs/Getting_Started/ZynqMPSoC-EDT/`
- **工具版本**: Vitis 2024.1 / PetaLinux 2024.1
- **说明**: 9章完整教程，从 Vivado Block Design 到 ZCU102 Linux 启动，是最权威的 ZCU102 入门资料
- **参考 TCL**: `ref_files/design1/edt_zcu102.tcl`
- **章节**:
  - Chapter 2: Getting Started（ZCU102 硬件要求，工具安装）
  - Chapter 3: System Configuration（Vivado 工程创建，PS 配置，XSA 导出）
  - Chapter 4: Build SW for PS Subsystems（A53/R5 裸机软件）
  - Chapter 5: Debugging with Vitis Debugger（JTAG 调试）
  - Chapter 8: Boot and Configuration（SD/QSPI/USB 启动）
  - Chapter 9: Secure Boot（安全启动实现）

## AMD 官方文档

| 文档编号 | 标题 | 下载地址 |
|----------|------|----------|
| UG1182 | ZCU102 Evaluation Board User Guide | https://docs.amd.com/r/en-US/ug1182-zcu102-eval-bd |
| UG1393 | Vitis Unified Software Platform Documentation | https://docs.amd.com/r/en-US/ug1393-vitis-application-acceleration |
| UG1144 | PetaLinux Tools Documentation Reference Guide | https://docs.amd.com/r/en-US/ug1144-petalinux-tools-reference-guide |
| UG1085 | Zynq UltraScale+ MPSoC Technical Reference Manual | https://docs.amd.com/r/en-US/ug1085-zynq-ultrascale-trm |
| UG1137 | Zynq UltraScale+ MPSoC Software Developer Guide | https://docs.amd.com/r/en-US/ug1137-zynq-ultrascale-mpsoc-swdev |

## 官方下载

- **Vivado 2023.1 统一安装器**: https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools/2023-1.html
- **PetaLinux 2023.1**: https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-design-tools/2023-1.html
- **ZCU102 BSP (2023.1)**: https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-design-tools/2023-1.html
  - 文件名: `xilinx-zcu102-v2023.1-05080224.bsp`
- **板卡文件**: https://github.com/Xilinx/XilinxBoardStore/tree/master/boards/Xilinx/zcu102
