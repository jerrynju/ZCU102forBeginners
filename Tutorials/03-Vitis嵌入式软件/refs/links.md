# 阶段 3 参考资源链接

## 核心官方教程

### 1. Vitis Embedded Software Getting Started（直接对应 ZCU102）
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Embedded_Software/Getting_Started/`
- **工具版本**: Vitis 2025.2
- **内容**: ZCU102 作为示例板，Vitis Platform 创建、Hello World on ARM、JTAG 调试、Flash 编程

### 2. ZCU102 嵌入式设计教程 Chapter 4-5
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: 
  - `docs/Getting_Started/ZynqMPSoC-EDT/4-build-sw-for-ps-subsystems.rst` — A53/R5 裸机软件
  - `docs/Getting_Started/ZynqMPSoC-EDT/5-debugging-with-vitis-debugger.rst` — JTAG 调试

### 3. Vitis 用户管理模式（命令行流程）
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Embedded_Software/Feature_Tutorials/01-user_managed_mode/`
- **内容**: xsct 脚本自动化，无 GUI 构建流程

### 4. embeddedsw 官方裸机示例
- **仓库**: https://github.com/Xilinx/embeddedsw
- **路径**: `lib/sw_apps/`
- **ZCU102 相关应用**:
  - `freertos_hello_world/` — FreeRTOS 入门（psu_cortexa53/psu_cortexr5）
  - `freertos_lwip_echo_server/` — FreeRTOS + LwIP TCP 服务器
  - `freertos_lwip_tcp_perf_client/` — TCP 性能测试客户端
  - `freertos_lwip_udp_perf_server/` — UDP 性能测试服务器
  - `zynqmp_fsbl/` — ZCU102 FSBL（第一阶段引导加载程序）
  - `zynqmp_pmufw/` — 平台管理单元固件
  - `zynqmp_dram_test/` — DDR 内存测试

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| UG1400 | Vitis Unified Embedded Software Development | Vitis 嵌入式开发完整手册 |
| UG1137 | Zynq UltraScale+ MPSoC Software Developer Guide | 多核启动流程，TCM/OCM 布局 |
| UG1198 | Zynq UltraScale+ MPSoC Processing System LogiCORE IP Product Guide | PS IP 参数详解 |
| UG643 | OS and Libraries Document Collection | FreeRTOS API on Zynq |
| UG1283 | Zynq UltraScale+ MPSoC Product Tables and Product Selection Guide | 器件选型 |
| PG201 | Zynq UltraScale+ RFSoC Register Reference | 寄存器映射 |

## FreeRTOS 参考
- **官网**: https://www.freertos.org/
- **Xilinx FreeRTOS 移植**: `embeddedsw/ThirdParty/bsp/freertos10_xilinx/`
- **API 文档**: https://www.freertos.org/Documentation/RTOS_book.html

## 版本说明
- Vitis 2024.1 之后从 Classic IDE 迁移到 Unified IDE
- 迁移指南: `Embedded_Software/Feature_Tutorials/03-vitis_classic_to_unified_migration/`
