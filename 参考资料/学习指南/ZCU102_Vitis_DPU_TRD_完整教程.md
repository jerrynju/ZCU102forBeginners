# ZCU102 Vitis DPU TRD 完整开发教程

> **基于 Vitis AI 3.0、Vitis 2022.2、XRT 2022.2**
> 
> 本文档是 ZCU102 开发板 Vitis 流程版 DPU-TRD 的完整教程，包含详细步骤、进阶参考和故障排查指南。

---

## 目录

- [项目概述](#项目概述)
- [硬件与软件要求](#硬件与软件要求)
- [核心操作步骤详解](#核心操作步骤详解)
- [Vitis 平台创建指南](#vitis-平台创建指南)
- [DPU IP 架构详解](#dpu-ip-架构详解)
- [调试与故障排查](#调试与故障排查)
- [常见问题与解决方案](#常见问题与解决方案)
- [进阶参考资源](#进阶参考资源)
- [附录：完整命令速查表](#附录完整命令速查表)

---

## 项目概述

### 项目背景

本项目是面向 ZCU102 开发板的 Vitis 流程版 DPU-TRD（Target Reference Design）扩展教程，基于 **Vitis AI 3.0**、**Vitis Tool 2022.2** 和 **XRT 2022.2** 实现。

### 核心改进点

相比 Xilinx 官方 Github 上的 Vitis-AI-DPU 教程，本教程做了以下定制化改进：

1. **DPU 架构优化**：将 DPU 架构从默认的 B4096 改为 **B512**，大幅缩短硬件设计编译时间（从数小时减少到约 40 分钟）
2. **预编译模型**：为 B512 DPU 重新编译了 ResNet50 模型（resnet50.xmodel），可直接使用
3. **完整日志**：包含完整的构建日志、启动日志和调试提示，便于问题排查
4. **适用性广**：适合自定义板卡的 DPU-TRD 开发参考

### 项目信息

- **作者**：LogicTronix（FPGA 设计 + 机器学习公司）
- **发布时间**：2023 年 3 月 27 日
- **开源协议**：GPL3+
- **难度等级**：中级
- **预计完成时间**：4 小时
- **原始教程链接**：https://www.hackster.io/LogicTronix/zcu102-vitis-dpu-trd-vitis-ai-3-0-c51609

---

## 硬件与软件要求

### 1.1 硬件组件

| 组件名称 | 数量 | 说明 |
|---------|------|------|
| Zynq UltraScale+ MPSoC ZCU102 开发板 | 1 | 核心开发板，需支持 SD 卡启动 |
| SD 卡（建议 16GB 以上） | 1 | 用于烧录系统镜像 |
| 串口线（USB 转 UART） | 1 | 用于查看板端启动日志 |
| 以太网线 | 1 | 可选，用于网络连接 |
| 电源适配器 | 1 | ZCU102 配套电源 |

### 1.2 软件环境

| 软件名称 | 版本要求 | 说明 |
|---------|----------|------|
| AMD Vitis Unified Software Platform | 2022.2 | 核心开发工具，用于硬件编译和平台构建 |
| Vitis AI | 3.0（DPU IP v4.1） | AI 模型编译、量化工具 |
| XRT（Xilinx Runtime） | 2022.2 | 板端运行时环境 |
| PetaLinux | 2022.2 | 用于生成 ZynqMP 通用镜像 |
| Balena Etcher | 任意版本 | SD 卡镜像烧录工具 |
| 串口终端工具 | 任意（GTKterm/Putty/TeraTerm 等） | 查看板端启动日志，波特率 115200 |

### 1.3 主机系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 18.04/20.04 | Ubuntu 20.04 LTS |
| CPU | 4 核 | 8 核以上 |
| 内存 | 16GB | 32GB 以上 |
| 硬盘 | 100GB 可用空间 | 200GB 以上 SSD |
| 显卡 | 无要求 | 无要求 |

---

## 核心操作步骤详解

### 步骤 A：准备基础平台与 ZynqMP 通用镜像

#### A.1 获取 ZCU102 基础平台

基础平台（Platform）是 Vitis 开发的核心，包含硬件描述、软件配置和启动文件。有三种获取方式：

**方式 1：从 Vitis 安装目录获取（推荐）**

```bash
# Vitis 安装目录下的基础平台路径
<Vitis_Installation_Directory>/Vitis/2022.2/base_platforms/xilinx_zcu102_base_202220_1
```

**方式 2：下载教程提供的打包基础平台**

- 教程提供了已打包的基础平台（本质是 Vitis 安装目录的拷贝）
- 下载后解压即可使用

**方式 3：自定义构建**

- 参考 [Xilinx Vitis 平台创建教程（ZCU104/KV260）](https://github.com/Xilinx/Vitis-Tutorials/tree/2022.2/Vitis_Platform_Creation)
- **注意**：ZCU102 的构建步骤与 ZCU104 完全一致，KV260 仅最后部分步骤有差异

#### A.2 下载 ZynqMP 通用镜像

ZynqMP 通用镜像是 PetaLinux 生成的标准 Linux 镜像，支持所有 Zynq UltraScale+ MPSoC 系列板卡。

**下载步骤**：

1. 访问 [PetaLinux 下载页面](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-platforms/2022-2.html)
2. 下载文件：`xilinx-zynqmp-common-v2022.2_10141622.tar.gz`
3. 解压到本地目录

**为什么需要这个镜像？**

- 该镜像包含 Linux 内核、设备树、根文件系统
- 后续构建硬件 Overlay 时需要引用该镜像中的软件组件
- 如果自行创建基础平台，需要手动生成该通用镜像

---

### 步骤 B：构建硬件 Overlay（核心步骤）

硬件 Overlay 是包含 DPU IP 的硬件设计，通过 Vitis 编译生成 `.xclbin` 文件，最终打包成 SD 卡镜像。

#### B.1 修改 DPU 架构为 B512

**为什么修改？**

- 默认 DPU 架构为 B4096（高算力），编译时间长达数小时
- B512（低算力）编译时间约 40 分钟，适合快速验证
- 验证通过后可再升级为高算力 DPU

**操作步骤**：

1. 打开文件：`DPUCZDX8G_VAI_v3.0/prj/Vitis/dpu_conf.vh`
2. 修改 DPU 架构定义：

```verilog
// 原始配置（B4096）
`define DPU_TARGET B4096

// 修改为（B512）
`define DPU_TARGET B512
```

**DPU 架构说明**：

- **B512**：低算力 DPU，编译速度快，适合开发和调试
- **B1024/B2048**：中等算力 DPU，平衡性能和编译时间
- **B4096**：高算力 DPU，适合高性能场景，但编译时间长

#### B.2 配置编译环境

在开始编译前，需要加载所有必要的环境变量：

```bash
# 1. 加载 XRT 环境（Xilinx Runtime）
source /opt/xilinx/xrt/setup.sh

# 2. 加载 Vitis 2022.2 环境
source <Vitis安装目录>/Vitis/2022.2/settings64.sh

# 3. 导出 ZynqMP 通用镜像路径
export EDGE_COMMON_SW=<通用镜像解压路径>/xilinx-zynqmp-common-v2022.2/

# 4. 导出 ZCU102 基础平台路径
export SDX_PLATFORM=<基础平台路径>/xilinx_zcu102_base_202220_1/xilinx_zcu102_base_202220_1.xpfm
```

**环境变量说明**：

- `EDGE_COMMON_SW`：指向 PetaLinux 生成的通用镜像，Vitis 需要从中提取 Linux 内核、设备树等
- `SDX_PLATFORM`：指向 Vitis 基础平台文件（.xpfm），定义了硬件平台和软件配置

#### B.3 执行编译

**编译命令**：

```bash
make all KERNEL=DPU DEVICE=zcu102
```

**编译过程详解**：

1. **Vivado 综合与实现**：将 DPU IP 集成到 Zynq MPSoC 硬件设计中，生成比特流（.bit 文件）
2. **v++ 编译**：将硬件设计打包成 .xclbin 文件（XRT 可加载的硬件镜像）
3. **打包 SD 卡镜像**：将比特流、xclbin、启动文件等打包成 sd_card.img

**编译时间**：

- B512 DPU：约 40 分钟
- B4096 DPU：约 3-4 小时

**编译输出**：

- 成功完成后，在 `binary_container_1` 目录下生成 `sd_card.img` 镜像文件
- 该镜像包含完整的启动系统，可直接烧录到 SD 卡

**常见问题**：

- **编译失败**：检查 Vitis 和 XRT 版本是否匹配（都必须是 2022.2）
- **内存不足**：硬件编译需要大量内存（建议 32GB 以上），如果内存不足可添加交换空间

---

### 步骤 C：ZCU102 开发板启动

#### C.1 烧录 SD 卡

**操作步骤**：

1. 插入 SD 卡到 PC
2. 打开 Balena Etcher 软件
3. 选择 `sd_card.img` 文件
4. 选择目标 SD 卡
5. 点击 "Flash" 开始烧录

**烧录完成后**：

- SD 卡会显示两个分区：`boot`（启动分区）和 `root`（根文件系统分区）
- `boot` 分区包含：BOOT.BIN、image.ub、boot.scr 等启动文件
- `root` 分区包含：完整的 Linux 文件系统

#### C.2 准备启动文件

为了后续调试和测试，需要将一些文件拷贝到 SD 卡的 `boot` 分区：

**需要拷贝的文件**：

1. **samples.zip**（应用示例）

```bash
# 压缩 samples 目录（包含符号链接，必须压缩）
cd DPUCZDX8G_VAI_v3.0/app
zip -r samples.zip samples/
```

2. **models.zip**（模型文件）

```bash
# 压缩 models 目录
zip -r models.zip models/
```

3. **dpu_sw_optimize.tar.gz**（root 分区扩容工具）
   - 该工具用于扩容 root 分区，解决默认 root 分区空间不足的问题

**拷贝到 boot 分区**：

- 将以上三个文件拷贝到 SD 卡的 `boot` 分区（可以通过文件管理器或命令行）

#### C.3 开发板启动配置

**1. 设置启动模式**

ZCU102 开发板支持多种启动模式，这里使用 SD 卡启动：

- **Rev 1.0 板卡**：设置 SW6 开关 [4:1] 为 `off, off, off, on`
- **其他版本**：参考 ZCU102 用户指南的启动模式设置表

**2. 连接硬件**

- 插入 SD 卡到 ZCU102 的 SD 卡插槽
- 连接电源适配器
- 连接 UART 串口线（USB 转 UART）到 PC
- 连接以太网线（可选）

**3. 配置串口终端**

- 打开串口终端工具（如 Putty、TeraTerm、GTKterm）
- 选择对应的 COM 端口（ZCU102 提供 4 个 UART 端口，通常选择端口 18）
- 设置波特率为 **115200**
- 数据位：8，停止位：1，奇偶校验：无，流控：无

#### C.4 首次启动操作

**1. 上电启动**

- 打开 ZCU102 电源开关
- 观察串口终端输出，等待 Linux 启动完成
- 首次启动会进入 Linux 登录界面

**2. 登录系统**

- 用户名：`root`
- 密码：（默认空密码，直接回车）

**3. 扩容 root 分区**

默认 root 分区空间较小，需要扩容以安装额外软件：

```bash
# 1. 将 dpu_sw_optimize.tar.gz 从 boot 分区拷贝到 home 目录
cp -r /run/media/mmcblk0p1/dpu_sw_optimize.tar.gz ~

# 2. 解压扩容工具
tar -xzf dpu_sw_optimize.tar.gz

# 3. 运行扩容脚本
cd dpu_sw_optimize
bash optimize_script.sh
```

**扩容脚本功能**：

- 自动检测 root 分区大小
- 将 root 分区扩展到 SD 卡的最大可用空间
- 重启后生效

**4. 解压应用示例和模型**

```bash
# 1. 拷贝 samples.zip 和 models.zip 到 home 目录
cp /run/media/mmcblk0p1/samples.zip ~
cp /run/media/mmcblk0p1/models.zip ~

# 2. 解压文件
unzip samples.zip
unzip models.zip
```

**目录结构说明**：

- `samples/`：包含 ResNet50 等模型的推理示例代码
- `models/`：包含预训练的 AI 模型文件（.xmodel）

---

### 步骤 D：为当前 DPU 架构编译 ResNet50 模型

#### D.1 为什么需要重新编译模型？

**问题背景**：

- DPU 架构（B512）改变后，硬件计算方式发生变化
- 预编译的 ResNet50 模型是基于 B4096 架构编译的
- 模型与 DPU 架构不匹配会导致 "指纹不匹配" 错误

**指纹（Fingerprint）机制**：

- 每个 DPU 架构有唯一的指纹标识
- 模型编译时会嵌入目标 DPU 的指纹
- 运行时检查模型指纹与 DPU 指纹是否匹配
- 不匹配则报错并终止运行

#### D.2 下载 ResNet50 模型

**模型来源**：

- 从 [Vitis AI Model Zoo](https://github.com/Xilinx/Vitis-AI/tree/master/model_zoo/model-list) 下载
- 选择 TensorFlow 版本的 ResNet50 模型

**推荐模型**：

- 模型名称：`tf_resnetv1_50_imagenet_224_224_6.97G_3.0`
- 版本：未剪枝（非 pruned）
- 输入尺寸：224x224
- 计算量：6.97GOPS

**下载步骤**：

1. 访问 Vitis AI Model Zoo 页面
2. 搜索 "resnet50"
3. 下载 TensorFlow 版本的模型文件
4. 解压到本地目录

**注意**：

- Vitis AI 2.5 之后不再支持 Caffe/Darknet 模型
- 仅支持 TensorFlow（v1/v2）和 PyTorch 模型

#### D.3 准备 arch.json 文件

`arch.json` 文件描述 DPU 架构信息，用于模型编译时生成正确的硬件指令。

**获取方式 1：从编译输出获取（推荐）**

在步骤 B 编译硬件 Overlay 时，会在 `binary_container_1/sd_card` 目录生成 `arch.json` 文件。

**获取方式 2：手动创建**

如果找不到生成的 `arch.json`，可以手动创建：

```json
{
  "fingerprint": "0x101000056010200"
}
```

**指纹说明**：

- `0x101000056010200` 对应 B512 DPU 架构、Vitis AI 3.0（DPU IP v4.1）
- 如果使用其他 DPU 架构，指纹会不同
- 指纹错误会导致模型无法运行

#### D.4 编译模型

**编译工具**：

- 使用 Vitis AI 2.5 及以上版本的 `vai_c_tensorflow` 工具
- **注意**：Vitis AI 1.4 不支持 DPU IP v4.1 的新特性，无法识别该指纹

**编译命令**：

```bash
vai_c_tensorflow \
  --arch ./arch_zcu102_2xb512_march2023.json \
  -f quantized/quantized_baseline_6.96B_919.pb \
  --output_dir compile_result_zcu102 \
  -n tf_resnet50
```

**参数说明**：

- `--arch`：指定 DPU 架构文件（arch.json）
- `-f`：指定量化后的 TensorFlow 模型文件（.pb）
- `--output_dir`：指定编译结果输出目录
- `-n`：指定输出模型名称

**编译过程**：

1. 读取量化模型（.pb 文件）
2. 根据 arch.json 生成 DPU 指令
3. 优化计算图
4. 生成 .xmodel 文件（Xilinx 模型格式）

**编译输出**：

- 在 `compile_result_zcu102` 目录下生成 `tf_resnet50.xmodel` 文件
- 该文件包含 DPU 可执行的指令和数据

#### D.5 重命名并拷贝模型

**重命名模型**：

```bash
cd compile_result_zcu102
mv tf_resnet50.xmodel resnet50.xmodel
```

**拷贝到 ZCU102**：

1. 将 `resnet50.xmodel` 拷贝到 SD 卡的 `boot` 分区
2. 可以通过读卡器拷贝，也可以通过网络拷贝（如果 ZCU102 已联网）

---

### 步骤 E：运行 Demo 验证

#### E.1 启动 ZCU102

**操作步骤**：

1. 将拷贝了新编译 `resnet50.xmodel` 的 SD 卡插入 ZCU102
2. 上电启动
3. 等待 Linux 启动完成（约 1-2 分钟）

#### E.2 运行 ResNet50 推理测试

**1. 登录系统**

```bash
ZCU102 login: root
Password: (直接回车)
```

**2. 查看当前目录文件**

```bash
ls
```

应该看到以下目录：

- `samples/`：应用示例代码
- `models/`：模型文件（可能为空）
- `dpu_sw_optimize/`：扩容工具

**3. 拷贝模型到 home 目录**

```bash
cp /run/media/mmcblk0p1/resnet50.xmodel ~
ls -lh resnet50.xmodel
```

**4. 运行 ResNet50 推理示例**

```bash
env LD_LIBRARY_PATH=samples/lib \
    XILINX_VART_FIRMWARE=/run/media/mmcblk0p1/dpu.xclbin \
    samples/bin/resnet50 img/bellpepper-994958.JPEG
```

**命令说明**：

- `env LD_LIBRARY_PATH=samples/lib`：设置动态库路径，指向 samples 目录下的库文件
- `XILINX_VART_FIRMWARE=/run/media/mmcblk0p1/dpu.xclbin`：指定 DPU 固件（硬件镜像）路径
- `samples/bin/resnet50`：ResNet50 推理可执行文件
- `img/bellpepper-994958.JPEG`：测试图片路径

**预期输出**：

```
Image: img/bellpepper-994958.JPEG
Top 5 predictions:
1. bell pepper (class 945): 0.9876
2. cucumber (class 920): 0.0089
3. zucchini (class 951): 0.0023
...
Inference time: 12.34 ms
```

**结果解读**：

- 模型正确识别出图片是 "bell pepper"（甜椒）
- 置信度 98.76%
- 推理时间 12.34 毫秒

#### E.3 测试其他图片

`samples/img/` 目录下包含多张测试图片，可以逐一测试：

```bash
samples/bin/resnet50 img/ILSVRC2012_val_00000001.JPEG
samples/bin/resnet50 img/ILSVRC2012_val_00000002.JPEG
...
```

---

## Vitis 平台创建指南

> 本部分内容基于 [Xilinx Vitis-Tutorials - Vitis Platform Creation](https://deepwiki.com/Xilinx/Vitis-Tutorials/4-vitis-platform-creation)

### 什么是 Vitis 平台？

Vitis 平台是 AMD FPGA/自适应 SoC 上开发加速应用的基础底座，由 **硬件平台（HPFM）** 和 **软件平台（SPFM）** 两部分组成。

- **硬件部分**：以 Vivado 导出的 XSA（Xilinx Shell Archive）文件形式存在
- **软件部分**：包含操作系统、设备驱动、运行时库等组件

### 平台组件详细说明

#### 1. 硬件组件（XSA 文件）

由 Vivado 设计导出，核心定义内容：

- 处理系统配置：CPU、内存控制器等
- 加速内核的可编程逻辑接口
- 内存映射与地址空间分配
- 硬件接口与互联拓扑
- 时钟域划分
- 中断架构
- Versal 系列设备还包含 AI Engine 配置

#### 2. 软件组件

包含面向加速应用的完整软件栈：

- **操作系统**：支持 Linux、裸机、FreeRTOS
- **启动组件**：第一级引导加载程序（FSBL）、U-Boot 等
- **设备树规范（DTS/DTB）**
- **硬件设备驱动**
- **根文件系统**（Linux 平台）
- **运行时库**：XRT（硬件加速运行时）

> **评估阶段**：可使用 AMD 提供的预构建「通用镜像（Common Image）」
> **生产阶段**：需通过 PetaLinux 定制

### Vitis 平台创建详细步骤

#### 步骤 1：在 Vivado 中创建硬件设计

支持 3 种实现方式，可根据场景选择：

| 实现方式 | 适用场景 | 特点 |
|---------|----------|------|
| Vivado 可定制示例设计（CED） | 快速启动、标准评估板 | 基于 Versal 可扩展嵌入式平台示例，预配置对应板卡参数，开箱即用 |
| 从零创建 | 自定义板卡、特殊需求 | 通过 IP Integrator 搭建完整硬件设计，灵活性最高 |
| 修改现有设计 | 已有基础设计的迭代优化 | 基于现有工程调整，适配新需求 |

**硬件设计核心注意事项**：

- 数据传输用内存接口
- 组件间通信用 AXI 接口
- 不同时钟域的合理划分
- 控制功能的中断处理机制
- 外部接口的 I/O 配置

#### 步骤 2：生成 XSA 文件

硬件设计完成后导出流程：

1. 生成块设计（Generate Block Design）
2. 在 Vivado 中通过 `File -> Export -> Export Platform` 导出平台
3. 根据需求配置导出选项：
   - 支持硬件/硬件仿真
   - 预综合/后实现版本选择

#### 步骤 3：在 Vitis 中创建平台

Vitis IDE 操作流：

1. 新建平台组件（New Platform Component）
2. 导入步骤 2 生成的 XSA 文件
3. 配置软件参数：
   - 操作系统类型（Linux/裸机等）
   - 处理器选择（例如 `psv_cortexa72`）
   - 域配置（Domain Configuration）
   - 设备树参数设置
4. 配置软件组件路径：
   - BIF 文件（启动镜像配置文件）
   - 预构建镜像目录
   - 设备树二进制（DTB）文件路径

#### 步骤 4：平台验证

通过测试应用验证平台可用性：

1. 创建面向该平台的测试应用（例如向量加法示例）
2. 配置应用参数：sysroot、根文件系统、内核镜像路径
3. 编译应用
4. 测试执行：
   - **硬件仿真**：无需物理硬件，验证功能正确性，调试软硬件交互问题
   - **硬件执行**：生成 SD 卡镜像/编程文件，在目标板卡启动运行，验证实际性能、启动流程、系统稳定性
5. 结果校验：确认功能正确、性能符合预期

### 平台类型说明

#### 1. Flat 平台（静态平台）

- **特点**：硬件架构固定，无运行时重配置能力，创建和使用流程简单
- **适用场景**：
  - 加速器集合固定的应用
  - 全部加速器资源可放入 FPGA 的设计
  - 追求简单开发流程的项目

#### 2. DFX 平台（动态功能交换平台）

- **特点**：支持运行时重配置 FPGA 资源，可动态加载不同加速功能，资源利用率更高
- **适用场景**：
  - 需要切换不同加速功能的应用
  - 总资源需求超过 FPGA 可用资源的场景
  - 需要运行时适配不同工作负载的系统

### 平台定制化方法

#### 1. PetaLinux 定制化（生产级软件栈）

评估阶段使用通用镜像，生产阶段需通过 PetaLinux 定制软件组件，流程：

1. 基于 XSA 文件创建 PetaLinux 工程
2. 定制 Linux 内核配置
3. 修改根文件系统，仅保留所需软件包
4. 更新设备树规范（适配自定义硬件）
5. 编译 PetaLinux 工程，生成定制化软件组件
6. 将生成的组件导入 Vitis 平台创建流程

**PetaLinux 定制可实现能力**：

- 针对特定硬件的自定义内核配置
- 仅包含必要组件的最小化根文件系统
- 自定义设备驱动与内核模块
- 定制化启动流程

#### 2. 自定义 IP 集成

平台可扩展自定义 IP 核提供专用功能，流程：

1. 在 Vivado/Vitis HLS 中设计自定义 IP 核
2. 将 IP 添加到 Vivado 块设计中
3. 配置 IP 接口（AXI/AXI-Stream 等）
4. 更新平台硬件设计
5. 导出更新后的 XSA 文件
6. 基于新 XSA 重建 Vitis 平台

**自定义 IP 集成适用场景**：

- 专用数据处理功能
- 外部硬件的自定义接口
- 特定算法的优化加速器
- 高吞吐量的流接口应用

---

## DPU IP 架构详解

### DPUCZDX8G IP 架构概述

DPUCZDX8G 是 Xilinx 针对 Zynq UltraScale+ MPSoC 系列器件设计的 DPU（Deep Learning Processing Unit）IP，可搭配多种卷积架构来配置。

### 支持的架构类型

DPUCZDX8G IP 的架构包括：

| 架构 | 计算能力 | 编译时间 | 适用场景 |
|------|----------|----------|----------|
| B512 | 低 | 短（~40分钟） | 开发调试、快速验证 |
| B800 | 中低 | 中等 | - |
| B1024 | 中 | 中等 | 平衡性能和编译时间 |
| B1152 | 中高 | 较长 | - |
| B1600 | 高 | 长 | - |
| B2304 | 很高 | 很长 | - |
| B3136 | 超高 | 极长 | - |
| B4096 | 最高 | 极长（~3-4小时） | 生产部署、最高性能 |

### 架构选择建议

1. **开发阶段**：使用 B512 或 B1024，编译速度快，便于快速迭代
2. **性能测试阶段**：使用 B2048 或 B2304，平衡性能和编译时间
3. **生产部署阶段**：使用 B4096，获得最高推理性能

### DPU 配置参数

除了架构类型，DPU 还有其他重要配置参数：

- **RAM_USAGE**：RAM 使用方式（LOW/HIGH）
- **CHANNEL_AUGMENTATION**：通道增强功能
- **KERNEL_AUGMENTATION**：卷积核增强功能
- **DSP_USAGE**：DSP 使用方式

**重要提示**：只要改了 DPU 架构相关参数（例如 B4096 → B2304、1 核 → 2 核、RAM_USAGE_LOW → RAM_USAGE_HIGH、CHANNEL_AUGMENTATION 等），都应该重新导出新的 arch.json 再重新编译 xmodel，否则会出现指纹不匹配错误。

---

## 调试与故障排查

### F.1 应用运行错误排查

#### 错误类型 1：指纹不匹配（Fingerprint Mismatch）

**错误信息**：

```
W1119 17:26:32.613843 659 dpu_runner_base_imp.cpp:733] CHECK fingerprint fail! 
model_fingerprint 0x101000056010407 is un-matched with actual dpu_fingerprint 0x101000056010200. 
Please re-compile xmodel with dpu_fingerprint 0x101000056010200 and try again.
F1119 17:26:32.614053 659 dpu_runner_base_imp.cpp:695] fingerprint check failure.
```

**原因分析**：

- DPU 已正常工作（否则不会进行指纹检查）
- 模型与 DPU 架构不匹配
- 模型是基于 B4096 编译的，但当前 DPU 是 B512 架构

**解决方案**：

- 重新编译模型，使用正确的 arch.json（包含 B512 的指纹）

#### 错误类型 2：模型文件未找到（xmodel Error）

**错误信息**：

```
F1119 17:23:20.634860 644 serialize_v2.cpp:705] [UNILOG][FATAL][XIR_READ_PB_FAILURE][failed to read pb file] 
file = resnet50.xmodel
*** Check failure stack trace: ***
Aborted
```

**原因分析**：

- resnet50.xmodel 文件不存在
- 或应用程序无权限读取该文件

**解决方案**：

- 检查模型文件是否在当前目录：`ls -l resnet50.xmodel`
- 如果不在，拷贝模型到当前目录：`cp /run/media/mmcblk0p1/resnet50.xmodel .`
- 如果使用 sudo 运行，确保 sudo 环境下也能访问模型文件

#### 错误类型 3：DPU 错误（DPU Error）

**错误信息**：

- 应用运行时报 DPU 相关错误，如 "Failed to load DPU" 或 "DPU timeout"

**原因分析**：

- DPU 硬件设计有问题
- 或 XRT 驱动未正确加载

**解决方案**：

- 检查 `lsmod` 确认 zocl 模块是否加载
- 检查 `dmesg` 查看 DPU 加载日志
- 重新编译硬件 Overlay

### F.2 `lsmod` 命令检查

`lsmod` 命令显示当前加载的内核模块，用于确认 XRT 和 DPU 驱动是否正常加载。

**正常加载的模块**：

```bash
root@zcu102:~# lsmod
Module                  Size  Used by
zocl                  122880  0
mali                  606208  0
dmacpy                 16384  0
uio                    20480  1
```

**关键模块说明**：

- **zocl**：XRT 核心模块，提供用户空间访问硬件的接口
  - 如果缺少 zocl，说明 XRT 未正确安装或基础平台配置有误
- **mali**：Mali GPU 驱动（ZCU102 有 Mali-400 GPU）
- **dmacpy**：DMA 拷贝加速模块
- **uio**：用户空间 I/O 模块，用于 DPU 中断处理

**问题排查**：

- 如果缺少 `zocl` 模块：
  - 检查 XRT 是否正确安装：`rpm -qa | grep xrt`
  - 检查基础平台配置：确认 `xrt.ini` 文件存在且配置正确
  - 重新编译基础平台

### F.3 `dmesg` 命令检查

`dmesg` 命令显示内核日志，用于查看硬件初始化过程中的错误信息。

**正常日志**：

```
[    2.387117] ####### Dpu Loaded Successful ########
[    2.387130] xlnx-dpu 8f00000001000000.dpuczdx8g: DPU probe successful
```

**错误日志示例 1：资源无效**

```
[    2.387130] xlnx-dpu 8f00000001000000.dpuczdx8g: invalid resource
[    2.387142] xlnx-dpu: probe of 8f00000001000000.dpuczdx8g failed with error -12
```

**原因分析**：

- 设备树中 DPU 资源配置错误
- 内存地址、中断号等配置不正确

**解决方案**：

- 检查设备树源文件（.dts）
- 确认 DPU 的寄存器地址、中断号与硬件设计一致

**错误日志示例 2：内存分配失败**

```
[    2.456789] xlnx-dpu 8f00000001000000.dpuczdx8g: failed to allocate memory
[    2.456801] xlnx-dpu: probe of 8f00000001000000.dpuczdx8g failed with error -12
```

**原因分析**：

- 系统内存不足
- 或 DPU 的 CMA（Contiguous Memory Allocator）配置不正确

**解决方案**：

- 增加 CMA 内存：`bootargs` 中添加 `cma=512M`
- 检查设备树中 CMA 配置

### F.4 基础平台问题排查

如果 DPU 完全不工作，问题可能出在 Vitis 基础平台配置上。

**关键检查点**：

**1. 时钟配置**

- 检查基础平台中的时钟 ID 是否设置为 1、2、3
- DPU 需要 3 个时钟：时钟 0（系统时钟）、时钟 1（DPU 时钟）、时钟 2（数据搬运时钟）

**2. 中断配置**

- 检查 DPU 中断是否正确连接到 PS 端
- 中断号不能与其他设备冲突

**3. AXI 接口配置**

- 确认从 PS 端使能了 AXI 从接口
- 允许内核访问 DDR 内存

**检查工具**：

- 使用 Vitis Analyzer 打开基础平台（.xpfm 文件）
- 查看平台配置报告

---

## 常见问题与解决方案

### Q1：编译硬件 Overlay 时提示 "内存不足"

**错误信息**：

```
ERROR: Vivado Implementation failed due to insufficient memory
```

**解决方案**：

1. **增加物理内存**：建议使用 32GB 以上内存
2. **添加交换空间**：

```bash
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

3. **使用轻量 DPU**：使用 B512 而不是 B4096

### Q2：ZCU102 启动后无法登录

**问题描述**：

- 启动后显示登录界面，但输入 root 后无响应

**原因分析**：

- root 文件系统损坏
- SD 卡烧录不完整

**解决方案**：

1. 重新烧录 SD 卡镜像
2. 使用质量好的 SD 卡（Class 10 以上）
3. 检查 SD 卡是否有坏块：`fsck /dev/mmcblk0p2`

### Q3：运行应用时提示 "Cannot find DPU firmware"

**错误信息**：

```
ERROR: Cannot find DPU firmware: /run/media/mmcblk0p1/dpu.xclbin
```

**解决方案**：

1. 检查 `dpu.xclbin` 文件是否存在：`ls -l /run/media/mmcblk0p1/dpu.xclbin`
2. 如果不存在，重新编译硬件 Overlay 并烧录 SD 卡
3. 设置正确的环境变量：`export XILINX_VART_FIRMWARE=/run/media/mmcblk0p1/dpu.xclbin`

### Q4：模型推理结果不正确

**问题描述**：

- 模型能运行，但分类结果错误

**可能原因**：

1. 模型未正确量化
2. 输入图片预处理不正确
3. 模型与 DPU 架构不匹配

**排查步骤**：

1. 在 PC 上用 TensorFlow 运行原始模型，确认模型本身正确
2. 检查量化过程是否正确（使用 Vitis AI 量化工具）
3. 检查输入图片是否被正确预处理（resize、normalize 等）
4. 重新编译模型，确保使用正确的 arch.json

### Q5：如何升级到高算力 DPU（B4096）？

**操作步骤**：

1. 修改 `dpu_conf.vh`：将 B512 改为 B4096
2. 重新编译硬件 Overlay（耗时 3-4 小时）
3. 重新编译模型（使用 B4096 的 arch.json）
4. 重新烧录 SD 卡并测试

**注意事项**：

- B4096 编译时间很长，建议先用 B512 验证流程
- B4096 的功耗和散热要求更高，需确保 ZCU102 散热良好

---

## 进阶参考资源

### 官方文档

1. **Vitis Unified Software Platform Documentation**
   - 链接：https://docs.xilinx.com/r/en-US/ug1400-vitis-embedded
   - 说明：Vitis 统一软件平台官方文档

2. **Vitis AI User Guide**
   - 链接：https://docs.xilinx.com/r/en-US/ug1414-vitis-ai
   - 说明：Vitis AI 用户指南

3. **ZCU102 Evaluation Board User Guide**
   - 链接：https://www.xilinx.com/support/documentation/boards_and_kits/zcu102/ug1182-zcu102-eval-bd.pdf
   - 说明：ZCU102 评估板用户指南

4. **DPUCZDX8G Product Guide (PG338)**
   - 链接：https://docs.xilinx.com/r/zh-CN/pg338-dpu/DPUCZDX8G-%E6%9E%B6%E6%9E%84
   - 说明：DPU IP 产品指南，包含架构详细说明

### 社区资源

1. **Xilinx Vitis AI & AI 官方论坛**
   - 链接：https://support.xilinx.com/s/topic/0TO2E000000YKY9WAO/vitis-ai-ai
   - 说明：官方技术支持论坛

2. **Vitis AI Github Issues**
   - 链接：https://github.com/Xilinx/Vitis-AI/issues
   - 说明：Github 问题追踪，可查找同类问题的解决方案

3. **Xilinx Vitis-Tutorials Github**
   - 链接：https://github.com/Xilinx/Vitis-Tutorials
   - 说明：Vitis 教程仓库，包含平台创建、加速应用开发等示例

### 中文教程

1. **CSDN - ZCU102 开发环境一步搭建：新手必看指南**
   - 链接：https://wenku.csdn.net/column/3jbab9nikx
   - 说明：中文教程，介绍 ZCU102 开发环境搭建

2. **知乎 - 在 ZCU102 上跑人脸识别官方 demo**
   - 链接：https://zhuanlan.zhihu.com/p/486833560
   - 说明：实战教程，介绍如何在 ZCU102 上运行 Vitis AI demo

---

## 附录：完整命令速查表

### A. 环境配置

```bash
# 加载 XRT 环境
source /opt/xilinx/xrt/setup.sh

# 加载 Vitis 环境
source /opt/xilinx/Vitis/2022.2/settings64.sh

# 导出环境变量
export EDGE_COMMON_SW=/path/to/xilinx-zynqmp-common-v2022.2/
export SDX_PLATFORM=/path/to/xilinx_zcu102_base_202220_1/xilinx_zcu102_base_202220_1.xpfm
```

### B. 编译硬件 Overlay

```bash
# 进入 DPU 目录
cd DPUCZDX8G_VAI_v3.0/prj/Vitis

# 修改 DPU 架构（编辑 dpu_conf.vh）
vi dpu_conf.vh

# 编译
make all KERNEL=DPU DEVICE=zcu102

# 编译输出：binary_container_1/sd_card.img
```

### C. ZCU102 启动后操作

```bash
# 扩容 root 分区
cp /run/media/mmcblk0p1/dpu_sw_optimize.tar.gz ~
tar -xzf dpu_sw_optimize.tar.gz
cd dpu_sw_optimize
bash optimize_script.sh

# 解压 samples 和 models
cp /run/media/mmcblk0p1/samples.zip ~
cp /run/media/mmcblk0p1/models.zip ~
unzip samples.zip
unzip models.zip
```

### D. 编译 ResNet50 模型

```bash
# 使用 Vitis AI 编译模型
vai_c_tensorflow \
  --arch ./arch_zcu102_2xb512_march2023.json \
  -f quantized/quantized_baseline_6.96B_919.pb \
  --output_dir compile_result_zcu102 \
  -n tf_resnet50

# 重命名模型
cd compile_result_zcu102
mv tf_resnet50.xmodel resnet50.xmodel
```

### E. 运行推理测试

```bash
# 设置环境变量
export LD_LIBRARY_PATH=samples/lib
export XILINX_VART_FIRMWARE=/run/media/mmcblk0p1/dpu.xclbin

# 运行 ResNet50 推理
samples/bin/resnet50 img/bellpepper-994958.JPEG
```

### F. 调试命令

```bash
# 查看内核模块
lsmod

# 查看内核日志
dmesg | grep -i dpu
dmesg | grep -i zocl

# 查看 DPU 状态
xbutil examine

# 查看 XRT 版本
xrt-smi version
```

---

## 总结

本教程详细介绍了 ZCU102 开发板 Vitis DPU TRD 的完整开发流程，包括：

1. **环境准备**：安装 Vitis、Vitis AI、XRT 等工具
2. **平台构建**：创建或获取 ZCU102 基础平台
3. **硬件编译**：构建 DPU 硬件 Overlay
4. **板端部署**：烧录 SD 卡并在 ZCU102 上启动
5. **模型编译**：为当前 DPU 架构编译 AI 模型
6. **应用验证**：运行 demo 验证部署是否成功

### 关键注意事项

1. **修改 DPU 架构后必须重新编译 AI 模型**
   - 否则会出现指纹不匹配错误
   - 每次修改 `dpu_conf.vh` 后都要重新编译模型

2. **自行创建基础平台需严格按官方教程**
   - 时钟 ID 必须设置为 1、2、3
   - 中断配置必须正确
   - 必须从 PS 端使能 AXI 从接口

3. **编译硬件 Overlay 耗时较长**
   - 建议使用 B512 低算力 DPU 加快编译速度
   - 验证通过后再升级为高算力 DPU

4. **Vitis AI 版本兼容性**
   - Vitis AI 3.0 的 DPU IP v4.1 不支持 Vitis AI 1.4 及更早版本编译的模型
   - 最低需使用 Vitis AI 2.5 版本编译模型

### 进一步学习建议

1. **深入理理解 DPU 架构**：阅读 PG338 DPU 产品指南
2. **学习 Vitis 平台创建**：参考 Vitis-Tutorials 仓库
3. **探索更多 AI 模型**：尝试编译和运行其他 Vitis AI Model Zoo 中的模型
4. **优化性能**：尝试不同的 DPU 架构配置，找到性能和编译时间的最佳平衡点

---

**文档版本**：v1.0  
**最后更新**：2026 年 6 月 3 日  
**作者**：基于 Hackster.io 教程整理
