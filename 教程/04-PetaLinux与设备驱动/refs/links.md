# 阶段 4 参考资源链接

## 核心官方教程

### 1. ZCU102 嵌入式设计教程 Chapter 6-7
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**:
  - `docs/Getting_Started/ZynqMPSoC-EDT/6-build-linux-sw-for-ps.rst` — PetaLinux 工程创建，Linux 应用开发
  - `docs/Getting_Started/ZynqMPSoC-EDT/7-design1-using-gpio-timer-interrupts.rst` — GPIO/定时器/中断完整设计案例
- **工具版本**: Vitis 2024.1 / PetaLinux 2024.1

### 2. PetaLinux Customization 教程
- **仓库**: https://github.com/Xilinx/Vitis-Tutorials
- **路径**: `Vitis_Platform_Creation/Feature_Tutorials/02_petalinux_customization/`
- **内容**: PetaLinux rootfs/内核/DT 自定义，用于 Vitis 加速平台

### 3. Vitis Embedded 调试指南
- **仓库**: https://github.com/Xilinx/Embedded-Design-Tutorials
- **路径**: `docs/Debugging/Vitis_Embedded_Debugging_Guide/`
- **内容**: 裸机和 Linux 调试场景

## AMD 官方文档

| 文档编号 | 标题 | 说明 |
|----------|------|------|
| UG1144 | PetaLinux Tools Documentation Reference Guide | PetaLinux 完整命令参考 |
| UG1186 | Zynq UltraScale+ MPSoC Linux Drivers | 驱动开发指南 |
| UG1085 Chap.24 | TRM: Device Tree | DT 节点格式参考 |

## 关键 GitHub 仓库

| 仓库 | 用途 |
|------|------|
| https://github.com/Xilinx/linux-xlnx | Xilinx 官方 Linux 内核（含 ZCU102 DT）|
| https://github.com/Xilinx/u-boot-xlnx | U-Boot（ZCU102 板卡支持）|
| https://github.com/Xilinx/device-tree-xlnx | DT 生成工具 |
| https://github.com/Xilinx/embeddedsw | 驱动库（V4L2/CAN/ETH）|

## ZCU102 Linux DT 位置
```
linux-xlnx/arch/arm64/boot/dts/xilinx/
├── zynqmp-zcu102-rev1.0.dts    # ZCU102 Rev1.0 DT
├── zynqmp-zcu102-revA.dts      # Rev A
├── zynqmp.dtsi                  # ZynqMP 公共节点
└── zynqmp-clk-ccf.dtsi          # 时钟子树
```

## V4L2 视频驱动相关 IP
| IP 产品指南 | 说明 |
|------------|------|
| PG232 | MIPI CSI-2 RX Subsystem |
| PG286 | Demosaic IP |
| PG278 | Video Frame Buffer Write |
| PG270 | AXI4-Stream to Video Out |
| PG245 | HDMI 1.4/2.0 TX/RX Subsystem |
