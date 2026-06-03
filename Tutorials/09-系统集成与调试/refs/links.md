# 阶段 9 参考资源链接

## 核心官方教程

### 1. Vivado 调试分析教程
- **仓库**: https://github.com/Xilinx/Vivado-Design-Tutorials
- **路径**: `General/Design_Methodologies/Reset_Assesment/`（时序/复位方法论）
- **相关路径**: `UltraScalePlus/DFX/DFX_Decoupler/`（动态调试相关）

### 2. Vitis 软件性能分析
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: `docs/Debugging/Software_Profiling_Vitis/`
- **内容**: AXI CDMA 性能分析，ARM 核心性能计数器

### 3. Vitis Embedded 调试指南
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: `docs/Debugging/Vitis_Embedded_Debugging_Guide/`
- **内容**: 裸机/Linux 调试场景，交叉触发

### 4. 创建可调试的 FSBL
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: `docs/Debugging/Creating_Debuggable_FSBL/`
- **内容**: FSBL 初始化序列调试

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| PG172 | ILA Product Guide | ILA IP 完整手册 |
| PG159 | VIO Product Guide | VIO IP 手册 |
| UG908 | Vivado Design Suite: Programming and Debugging | ChipScope/硬件管理器 |
| UG936 | Vivado Design Suite Tutorial: Programming and Debugging | ILA/VIO 操作步骤 |
| UG1085 Chap.28 | TRM: Performance Monitoring Unit | PMU 性能计数器 |

## SWUpdate A/B OTA 升级

| 资源 | 说明 |
|------|------|
| https://sbabic.github.io/swupdate/ | SWUpdate 官方文档 |
| https://github.com/sbabic/swupdate | SWUpdate 源码 |
| PetaLinux: CONFIG_SWUPDATE | PetaLinux 中启用 SWUpdate |
| UG1144 Chapter 9 | PetaLinux rootfs 软件包添加 |

## 系统调试工具箱

```bash
# === ILA 相关（Vivado Tcl）===
# 连接板卡
open_hw_manager
connect_hw_server
open_hw_target

# 获取 ILA 列表
get_hw_ilas

# 配置触发并运行
run_hw_ila [get_hw_ilas hw_ila_1]
wait_on_hw_ila [get_hw_ilas hw_ila_1]
upload_hw_ila_data [get_hw_ilas hw_ila_1]

# === Linux 性能工具 ===
perf top                              # 实时 CPU 热点
perf stat -a sleep 10                 # 系统性能计数器
strace -c ./your_app                  # 系统调用统计
valgrind --tool=massif ./your_app     # 内存使用分析
cat /proc/interrupts                  # 中断统计

# === DPU 调试 ===
# 查看 DPU 版本和状态
cat /sys/devices/platform/amba/*/dpucore/version

# DNNDK 性能分析
LD_PRELOAD=/usr/lib/libdpuaol.so ./your_dpu_app

# === 系统资源监控 ===
htop                                  # CPU/内存
iotop                                 # I/O
nethogs                               # 网络
free -m                               # 内存概况
vmstat 1                              # 虚拟内存统计
```
