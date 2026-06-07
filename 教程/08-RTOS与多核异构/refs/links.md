# 阶段 8 参考资源链接

## 核心官方教程

### 1. Introduction to OpenAMP（官方 OpenAMP 教程）
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Embedded_Software/Introduction_to_OpenAMP/`
  （注：旧路径 `Embedded_Software/Feature_Tutorials/` 下有相关内容）
- **内容**: A53 Linux master + R5 FreeRTOS remote，RPMsg 通信
- **工具版本**: Vitis 2025.2

### 2. embeddedsw OpenAMP 示例（ZCU102 已验证）
- **仓库**: https://github.com/Xilinx/embeddedsw
- **关键路径**:
  - `lib/sw_apps/openamp_echo_test/src/machine/zynqmp_r5/` — ZCU102 R5 支持已确认
  - `lib/sw_apps/openamp_matrix_multiply/` — OpenAMP 矩阵乘法演示
  - `lib/sw_apps/openamp_rpc_demo/` — 远程过程调用演示
  - `lib/sw_apps/libmetal_echo_demo/` — libmetal 共享内存回环
  - `lib/sw_apps/freertos_hello_world/` — FreeRTOS 入门（psu_cortexr5）
  - `lib/sw_apps/freertos_lwip_echo_server/` — FreeRTOS TCP 服务器

### 3. ZCU102 嵌入式设计教程（多核章节）
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: `docs/Getting_Started/ZynqMPSoC-EDT/4-build-sw-for-ps-subsystems.rst`
- **内容**: A53 + R5 双核 BOOT.BIN 生成

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| UG1137 | Zynq UltraScale+ MPSoC Software Developer Guide | 多核启动, TCM/OCM 布局, OpenAMP 集成 |
| UG1085 Chap.5 | TRM: RPU (Real-time Processing Unit) | R5 架构, TCM, 看门狗, Lockstep |
| UG1085 Chap.6 | TRM: System Memory Map | OCM/DDR 地址映射 |
| UG1085 Chap.19 | TRM: IPI (Inter-Processor Interrupts) | A53-R5 中断通知机制 |
| UG643 | OS and Libraries Document Collection | FreeRTOS API 参考 |

## 关键 GitHub 仓库

| 仓库 | 用途 |
|------|------|
| https://github.com/OpenAMP/open-amp | OpenAMP 库（Xilinx 集成版本）|
| https://github.com/OpenAMP/libmetal | Metal 抽象层（用于 OpenAMP）|
| https://github.com/FreeRTOS/FreeRTOS | FreeRTOS 主仓库 |

## OCM 与 RPMsg 内存布局

```
Zynq UltraScale+ OCM（256KB, 0xFFFC0000-0xFFFFFFFF）:
  0xFFFC0000  VirtIO Ring Buffer 0 (A53 → R5, 4KB)
  0xFFFC1000  VirtIO Ring Buffer 1 (R5 → A53, 4KB)
  0xFFFC2000  RPMsg 消息缓冲区 (252×256B = 63KB)
  0xFFFD0000  实时状态共享区（无锁读，64KB）
  0xFFFE0000  R5 中断向量表（必须映射到低地址）
  0xFFFF0000  系统控制（PMU/FSBL 保留）

TCM (ZCU102 R5_0):
  0x00000000  ATCM 64KB（代码，零等待时间）
  0x00020000  BTCM 64KB（数据，零等待时间）
  0x00100000  DDR 起始（需要总线仲裁，较慢）
```

## 实时性验证

```bash
# Linux 侧使用 cyclictest 测量中断延迟
sudo apt install rt-tests
cyclictest -t 1 -p 80 -n -i 1000 -l 10000 -D 10

# 期望值（R5 FreeRTOS，ATCM 中断处理）：
# Min: 3μs, Avg: 8μs, Max: <200μs（无负载）
```
