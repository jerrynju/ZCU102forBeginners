# 阶段 1：环境搭建与工具链

## 学习目标

完成本阶段后，你将能够：
- 在 Ubuntu 20.04/22.04 上完整安装 Vivado / Vitis / PetaLinux 2023.1
- 配置 License（设计套件 + DPU IP）
- 在 ZCU102 上烧录预制 BSP，完成第一次 "Hello World" 上板运行
- 理解工具链各组件的职责和调用关系

---

## 1.1 工具链架构

```
┌─────────────────────────────────────────────────────┐
│  AMD Xilinx 2023.1 统一安装器                        │
│                                                     │
│  Vivado ML Edition          Vitis HLS               │
│  ├── Synthesis/P&R          ├── C→RTL 综合           │
│  ├── IP Integrator (IPI)    └── 仿真/Co-Sim          │
│  └── Hardware Manager                               │
│                                                     │
│  Vitis Unified IDE          PetaLinux 2023.1        │
│  ├── Platform (XSA)         ├── Yocto 构建系统        │
│  ├── Domain (BSP/OS)        ├── 内核/U-Boot          │
│  └── Application            └── rootfs              │
│                                                     │
│  Vitis AI 3.5                                       │
│  ├── Docker 量化工具链                               │
│  ├── DPU B4096 IP                                   │
│  └── VART 运行时                                    │
└─────────────────────────────────────────────────────┘
```

---

## 1.2 安装步骤

### 1.2.1 系统准备

```bash
# Ubuntu 22.04 依赖
sudo apt-get update
sudo apt-get install -y \
    gcc g++ make cmake git \
    libncurses5-dev libssl-dev \
    python3-pip python3-venv \
    libtinfo5 libstdc++6 \
    default-jre \
    net-tools libgl1-mesa-glx \
    texinfo chrpath socat cpio \
    diffstat unzip rsync
```

### 1.2.2 下载统一安装器

从 AMD 官网下载 `Xilinx_Unified_2023.1_*.bin`（约 120 GB 解压后）：

```bash
chmod +x Xilinx_Unified_2023.1_*.bin
./Xilinx_Unified_2023.1_*.bin
# 选择：Vitis（自动包含 Vivado）
# 安装路径建议：/tools/Xilinx
# 勾选组件：Vivado ML Standard + Vitis + Vitis HLS
```

### 1.2.3 环境变量

```bash
# 加入 ~/.bashrc
source /tools/Xilinx/Vivado/2023.1/settings64.sh
source /tools/Xilinx/Vitis/2023.1/settings64.sh

# PetaLinux（单独安装包）
source /opt/petalinux-2023.1/settings.sh
```

### 1.2.4 License 配置

```bash
# 节点锁 License（固定于主机 MAC 地址）
export XILINXD_LICENSE_FILE=/tools/Xilinx/license/Xilinx.lic

# 或浮动 License
export XILINXD_LICENSE_FILE=27000@license_server_ip
```

> **注意**：DPU IP (PG338) 需要单独的 Vitis AI License，可在 AMD 官网免费申请。

---

## 1.3 ZCU102 板卡初始化

### 1.3.1 SD 卡烧录（预制 BSP）

下载 ZCU102 官方 BSP（包含 BOOT.BIN + 内核 + rootfs）：

```bash
# 官方预制 PetaLinux 2023.1 BSP
# 下载：xilinx-zcu102-v2023.1-05080224.bsp

# 方式一：使用 balenaEtcher 烧录到 microSD
# 方式二：手动分区
sudo parted /dev/sdX mklabel msdos
sudo parted /dev/sdX mkpart primary fat32 1MiB 512MiB   # boot分区
sudo parted /dev/sdX mkpart primary ext4 512MiB 100%     # rootfs
sudo mkfs.vfat -n BOOT /dev/sdX1
sudo mkfs.ext4 -L rootfs /dev/sdX2
```

### 1.3.2 拨码开关设置（SD 卡启动）

ZCU102 SW6 拨码开关（从左到右 1-4）：

```
SD 卡启动：1=OFF  2=OFF  3=OFF  4=ON
JTAG 调试：1=ON   2=OFF  3=OFF  4=OFF
```

### 1.3.3 串口连接（UART0）

```bash
sudo apt install minicom
sudo minicom -D /dev/ttyUSB0 -b 115200

# 或使用 picocom
sudo picocom /dev/ttyUSB0 -b 115200
```

---

## 1.4 第一个项目：Hello World (Standalone)

### 1.4.1 新建 Vivado 工程

```tcl
# Vivado Tcl 脚本（refs/create_hello_world.tcl）
create_project hello_zcu102 ./hello_zcu102 -part xczu9eg-ffvb1156-2-e
set_property board_part xilinx.com:zcu102:part0:3.4 [current_project]

# 创建 Block Design
create_bd_design "system"
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 zynq_ultra_ps_e_0

# 自动连接 PS
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset 1} [get_bd_cells zynq_ultra_ps_e_0]

# 生成 XSA
make_wrapper -files [get_files system.bd] -top
add_files -norecurse ./hello_zcu102/hello_zcu102.gen/sources_1/bd/system/hdl/system_wrapper.v
launch_runs impl_1 -to_step write_device_image
write_hw_platform -fixed -force -file ./zcu102_hello.xsa
```

### 1.4.2 Vitis 应用创建

```bash
# 新建 Platform
vitis -s refs/create_platform.py

# 或在 Vitis GUI 中：
# File > New > Platform Project > 选择 zcu102_hello.xsa
# File > New > Application Project > Hello World
```

### 1.4.3 板卡运行结果

UART 终端应输出：
```
Xilinx Zynq MP First Stage Boot Loader
...
Hello World from ZCU102!
```

---

## 1.5 验证清单

- [ ] Vivado 2023.1 安装成功，可打开 GUI
- [ ] Vitis 2023.1 安装成功，能创建 Platform/Application
- [ ] PetaLinux 2023.1 安装成功，`petalinux-build --version` 返回正确版本
- [ ] ZCU102 可通过串口输出 U-Boot 启动信息
- [ ] Hello World 程序在板卡上运行成功
- [ ] License 配置正确（`vlm status` 显示有效）

---

## 参考资源

| 资源 | 链接 | 说明 |
|------|------|------|
| Vitis 统一 IDE 安装手册 | UG1393 | 官方安装步骤 |
| ZCU102 板卡手册 | UG1182 | 板卡原理图、启动模式 |
| PetaLinux 工具参考 | UG1144 | PetaLinux 命令参考 |
| 官方 BSP 下载 | [downloads.xilinx.com](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-design-tools.html) | 2023.1 BSP |

详见 [`refs/`](refs/) 目录中的参考设计文件。
