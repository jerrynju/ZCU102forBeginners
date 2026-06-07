# ZCU102 Vitis DPU TRD 入门指南

> **适合对象**：FPGA 和 AI 加速入门者  
> **阅读时间**：约 30 分钟  
> **学习目标**：理解 ZCU102 DPU 开发的基本概念和整体流程

---

## 目录

- [前言](#前言)
- [第一部分：基础概念](#第一部分基础概念)
- [第二部分：开发流程概览](#第二部分开发流程概览)
- [第三部分：详细步骤指引](#第三部分详细步骤指引)
- [第四部分：常见问题解答](#第四部分常见问题解答)
- [第五部分：学习资源推荐](#第五部分学习资源推荐)
- [附录：术语表](#附录术语表)

---

## 前言

### 这份指南适合你吗？

如果你符合以下情况，这份指南正是为你准备的：

- ✅ 刚接触 Xilinx ZCU102 开发板
- ✅ 想了解如何在 FPGA 上部署 AI 模型
- ✅ 对 Vitis、Vitis AI、DPU 等术语感到陌生
- ✅ 需要一份循序渐进的入门教程

### 你将学到什么？

通过这份指南，你将理解：

1. **ZCU102 开发板**是什么，它能做什么
2. **Vitis AI** 是什么，如何帮助部署 AI 模型
3. **DPU（深度学习处理单元）** 是什么，如何工作
4. 从零开始到成功运行 AI 推理的**完整流程**
5. 如何**排查常见问题**

### 学习路径建议

```
第 1 周：阅读本指南，理解基础概念
第 2 周：按照完整教程（ZCU102_Vitis_DPU_TRD_完整教程.md）实际操作
第 3 周：尝试修改 DPU 配置，编译不同架构
第 4 周：尝试部署自己的 AI 模型
```

---

## 第一部分：基础概念

### 1.1 什么是 ZCU102？

**ZCU102** 是 Xilinx（现在叫 AMD）推出的一款**评估开发板**，用于快速原型开发和学习。

#### 核心特点

| 特点 | 说明 |
|------|------|
| **处理芯片** | Zynq UltraScale+ XCZU9EG（集成 FPGA + ARM 处理器） |
| **FPGA 资源** | 可编程逻辑（PL），可实现硬件加速 |
| **处理器** | ARM Cortex-A53（四核）+ Cortex-R5（双核） |
| **内存** | 4GB DDR4（PS 端）+ 512MB DDR4（PL 端） |
| **外设接口** | USB、以太网、SD 卡、PCIe、SATA 等 |

#### 为什么选择 ZCU102？

- **功能强大**：FPGA + ARM 的异构架构，既能做硬件加速，又能运行 Linux 系统
- **生态成熟**：Xilinx 官方支持，有大量教程和参考设计
- **适合学习**：评估板设计，接口丰富，适合原型开发

#### ZCU102 能做什么？

- ✅ **AI 推理加速**：在 FPGA 上部署深度学习模型（本教程的重点）
- ✅ **信号处理**：图像处理、雷达信号处理、通信信号处理
- ✅ **嵌入式计算**：运行 Linux 系统，作为嵌入式计算平台
- ✅ **原型验证**：验证自定义 IP 核或算法

---

### 1.2 什么是 Vitis？

**Vitis** 是 Xilinx 推出的**统一软件平台**，用于开发 FPGA 加速应用。

#### Vitis 的核心组成

```
Vitis 统一软件平台
├── Vitis IDE          # 集成开发环境
├── Vitis HLS         # 高级综合工具（C/C++ → RTL）
├── Vitis Analyzer    # 性能分析工具
└── Vitis Libraries   # 加速库（视觉、金融、量化等）
```

#### Vitis 能做什么？

| 功能 | 说明 | 适用场景 |
|------|------|----------|
| **硬件加速** | 将计算密集型任务卸载到 FPGA | AI 推理、信号处理 |
| **软件开发** | 在 ARM 处理器上开发应用 | 嵌入式 Linux 应用 |
| **平台创建** | 创建自定义硬件平台 | 自定义板卡开发 |
| **系统集成** | 集成硬件加速器和软件应用 | 完整系统设计 |

#### Vitis 与传统 FPGA 开发的区别

| 传统 FPGA 开发 | Vitis 开发 |
|----------------|-------------|
| 使用 Verilog/VHDL 编程 | 使用 C/C++/OpenCL 编程 |
| 需要深入理解硬件时序 | 自动优化，无需手动时序约束 |
| 开发周期长（数周/数月） | 开发周期短（数天/数周） |
| 适合硬件专家 | 适合软件工程师 |

---

### 1.3 什么是 Vitis AI？

**Vitis AI** 是 Xilinx 推出的** AI 推理开发栈**，用于在 Xilinx 硬件平台上部署深度学习模型。

#### Vitis AI 的核心组件

```
Vitis AI 开发栈
├── AI 模型库（Model Zoo）     # 预训练模型（ResNet、YOLO 等）
├── 模型量化工具                # 浮点模型 → 定点模型
├── 模型编译工具                # 模型 → DPU 可执行文件
├── DPU IP                     # 深度学习处理单元（硬件加速器）
└── 运行时库（VART）          # 应用调用 DPU 的 API
```

#### Vitis AI 的工作流程

```
第 1 步：获取模型           → 从 Model Zoo 下载或训练自己的模型
第 2 步：量化模型           → 浮点模型（FP32）→ 定点模型（INT8）
第 3 步：编译模型           → 生成 DPU 可执行的 .xmodel 文件
第 4 步：部署到硬件         → 将模型烧录到 SD 卡
第 5 步：运行推理           → 应用调用 DPU 执行推理
```

#### 为什么需要 Vitis AI？

- **简化部署**：无需手动优化模型，工具链自动完成
- **高性能**：DPU 专用硬件加速，性能远超 CPU
- **支持主流框架**：TensorFlow、PyTorch、Caffe 等
- **丰富的模型库**：Model Zoo 提供大量预训练模型

---

### 1.4 什么是 DPU？

**DPU（Deep Learning Processing Unit）** 是 Xilinx 设计的**可编程深度学习加速器 IP**，部署在 FPGA 的逻辑资源中。

#### DPU 的工作原理

```
输入图片 → 预处理 → DPU 推理 → 后处理 → 输出结果
            ↓
          ARM CPU    DPU (FPGA)    ARM CPU
```

#### DPU 的架构类型

DPU 有多种架构配置，主要影响**算力**和**编译时间**：

| 架构 | 算力 | 编译时间 | 推荐用途 |
|------|------|----------|----------|
| **B512** | 低 | 短（~40 分钟） | 开发调试 |
| **B1024** | 中 | 中等 | 平衡选择 |
| **B4096** | 高 | 长（~3-4 小时） | 生产部署 |

**本教程选择 B512 的原因**：编译速度快，适合学习和调试。

#### DPU 的关键概念

1. **指纹（Fingerprint）**
   - 每个 DPU 架构有唯一的指纹标识
   - 模型编译时会嵌入目标 DPU 的指纹
   - 运行时检查指纹是否匹配，不匹配则报错

2. **Overlay**
   - 包含 DPU IP 的硬件设计
   - 编译后生成 .xclbin 文件
   - 最终打包到 SD 卡镜像中

3. **XModel**
   - Vitis AI 编译生成的模型文件
   - 包含 DPU 可执行的指令和数据
   - 需要与 DPU 架构匹配

---

### 1.5 核心概念关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    ZCU102 开发板                          │
│  ┌─────────────────┐      ┌─────────────────┐          │
│  │   ARM CPU        │      │   FPGA (PL)      │          │
│  │   (PS 端)       │◄────►│   (PL 端)       │          │
│  │   - 运行 Linux   │      │   - 部署 DPU     │          │
│  │   - 控制程序     │      │   - 加速推理     │          │
│  └─────────────────┘      └─────────────────┘          │
│           ▲                        ▲                       │
│           │                        │                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Vitis AI 工具链                        │ │
│  │  - 量化工具（Quantizer）                          │ │
│  │  - 编译工具（Compiler）                           │ │
│  │  - 运行时库（VART）                              │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 第二部分：开发流程概览

### 2.1 整体流程图

```
开始
 │
 ▼
[步骤 1] 准备开发环境
 ├── 安装 Vitis 2022.2
 ├── 安装 Vitis AI 3.0
 └── 安装 XRT 2022.2
 │
 ▼
[步骤 2] 获取基础平台
 ├── 从 Vitis 安装目录获取，或
 ├── 下载教程提供的平台，或
 └── 自行创建平台（复杂）
 │
 ▼
[步骤 3] 构建硬件 Overlay
 ├── 修改 DPU 架构为 B512
 ├── 配置编译环境变量
 └── 执行编译（约 40 分钟）
 │
 ▼
[步骤 4] 烧录 SD 卡
 ├── 使用 Balena Etcher 烧录 sd_card.img
 └── 拷贝 samples.zip、models.zip、dpu_sw_optimize.tar.gz
 │
 ▼
[步骤 5] ZCU102 首次启动
 ├── 设置 SD 卡启动模式
 ├── 连接串口终端（115200 波特率）
 ├── 登录系统（root / 无密码）
 └── 扩容 root 分区
 │
 ▼
[步骤 6] 编译 AI 模型
 ├── 下载 ResNet50 模型
 ├── 准备 arch.json（DPU 架构描述）
 └── 编译模型（生成 resnet50.xmodel）
 │
 ▼
[步骤 7] 运行 Demo 验证
 ├── 拷贝 resnet50.xmodel 到 ZCU102
 ├── 设置环境变量
 └── 运行推理测试
 │
 ▼
成功！🎉
```

### 2.2 各步骤预计时间

| 步骤 | 内容 | 预计时间 | 难度 |
|------|------|----------|------|
| 步骤 1 | 准备开发环境 | 2-4 小时 | ⭐⭐ |
| 步骤 2 | 获取基础平台 | 30 分钟 | ⭐ |
| 步骤 3 | 构建硬件 Overlay | 1-2 小时（含编译等待） | ⭐⭐⭐ |
| 步骤 4 | 烧录 SD 卡 | 30 分钟 | ⭐ |
| 步骤 5 | ZCU102 首次启动 | 30 分钟 | ⭐⭐ |
| 步骤 6 | 编译 AI 模型 | 1 小时 | ⭐⭐⭐ |
| 步骤 7 | 运行 Demo 验证 | 30 分钟 | ⭐ |

**总计**：约 6-8 小时（首次操作，含等待编译时间）

### 2.3 可能遇到的挑战

| 挑战 | 发生概率 | 解决方法 |
|------|----------|----------|
| 编译时内存不足 | 高 | 增加交换空间，或使用 B512 架构 |
| SD 卡烧录失败 | 中 | 更换 SD 卡，或使用质量更好的卡 |
| 模型与 DPU 不匹配 | 高 | 重新编译模型，确保 arch.json 正确 |
| ZCU102 无法启动 | 中 | 检查 SW6 开关设置，重新烧录 SD 卡 |
| 应用运行时报错 | 中 | 查看 `dmesg` 日志，检查 `lsmod` |

---

## 第三部分：详细步骤指引

> **注意**：本部分是简化版步骤指引，详细操作步骤请参考《ZCU102_Vitis_DPU_TRD_完整教程.md》

### 步骤 1：准备开发环境

#### 1.1 安装 Vitis 2022.2

**下载链接**：https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vitis/2022-2.html

**安装步骤**：

1. 下载 Vitis 安装程序（约 30GB）
2. 运行安装程序：`xsetup.exe`（Windows）或 `xsetup`（Linux）
3. 选择 "Vitis Unified Software Platform"
4. 选择安装目录（建议：`C:\Xilinx` 或 `/opt/Xilinx`）
5. 等待安装完成（约 1-2 小时）

**验证安装**：

```bash
# Linux 下验证
source /opt/Xilinx/Vitis/2022.2/settings64.sh
vitis -version
```

#### 1.2 安装 Vitis AI 3.0

**方式 1：从 Github 克隆（推荐）**

```bash
git clone https://github.com/Xilinx/Vitis-AI.git
cd Vitis-AI
git checkout v3.0
```

**方式 2：下载发布包**

从 https://github.com/Xilinx/Vitis-AI/releases/tag/v3.0 下载

#### 1.3 安装 XRT 2022.2

**下载链接**：https://github.com/Xilinx/XRT/releases/tag/2022.2

**安装步骤**：

```bash
# Ubuntu/Debian
sudo apt install ./xrt_202220.2.14.0_18.04-amd64.deb

# CentOS/RHEL
sudo yum install ./xrt_202220.2.14.0_7.x86_64.rpm
```

**验证安装**：

```bash
xrt-smi version
```

---

### 步骤 2：获取基础平台

#### 2.1 推荐方式：从 Vitis 安装目录获取

```bash
# 基础平台路径
<Vitis_Installation_Directory>/Vitis/2022.2/base_platforms/xilinx_zcu102_base_202220_1
```

**检查是否存在**：

```bash
ls -la <Vitis_Installation_Directory>/Vitis/2022.2/base_platforms/
```

如果不存在，需要重新安装 Vitis，并勾选 "Base Platforms" 组件。

#### 2.2 下载 ZynqMP 通用镜像

**下载链接**：https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-platforms/2022-2.html

**文件名**：`xilinx-zynqmp-common-v2022.2_10141622.tar.gz`

**解压**：

```bash
tar -xzf xilinx-zynqmp-common-v2022.2_10141622.tar.gz
```

---

### 步骤 3：构建硬件 Overlay

#### 3.1 修改 DPU 架构

**为什么要修改？**

默认架构 B4096 编译时间太长（3-4 小时），B512 只需 40 分钟，适合学习。

**修改方法**：

1. 打开文件：`DPUCZDX8G_VAI_v3.0/prj/Vitis/dpu_conf.vh`
2. 找到行：`define DPU_TARGET B4096`
3. 改为：`define DPU_TARGET B512`
4. 保存文件

#### 3.2 配置环境变量

```bash
# 1. 加载 XRT
source /opt/xilinx/xrt/setup.sh

# 2. 加载 Vitis
source /opt/Xilinx/Vitis/2022.2/settings64.sh

# 3. 设置通用镜像路径
export EDGE_COMMON_SW=/path/to/xilinx-zynqmp-common-v2022.2/

# 4. 设置基础平台路径
export SDX_PLATFORM=/path/to/xilinx_zcu102_base_202220_1/xilinx_zcu102_base_202220_1.xpfm
```

#### 3.3 执行编译

```bash
cd DPUCZDX8G_VAI_v3.0/prj/Vitis
make all KERNEL=DPU DEVICE=zcu102
```

**编译过程**：

- 0-10 分钟：Vivado 综合
- 10-30 分钟：Vivado 实现
- 30-40 分钟：v++ 打包

**编译成功标志**：

```
*** Finished building target: binary_container_1/sd_card.img ***
```

---

### 步骤 4：烧录 SD 卡

#### 4.1 准备文件

编译完成后，在 `binary_container_1` 目录找到 `sd_card.img` 文件。

#### 4.2 使用 Balena Etcher 烧录

**下载链接**：https://www.balena.io/etcher/

**烧录步骤**：

1. 打开 Balena Etcher
2. 点击 "Flash from file"，选择 `sd_card.img`
3. 点击 "Select target"，选择 SD 卡
4. 点击 "Flash!" 开始烧录
5. 等待烧录完成（约 10-15 分钟）

#### 4.3 拷贝额外文件

烧录完成后，SD 卡会出现 `boot` 分区。

**需要拷贝的文件**：

1. `samples.zip`（从 `DPUCZDX8G_VAI_v3.0/app` 目录压缩）
2. `models.zip`（从 `DPUCZDX8G_VAI_v3.0/app` 目录压缩）
3. `dpu_sw_optimize.tar.gz`（从教程提供的数据包中获取）

**拷贝方法**：

- Windows：直接复制粘贴到 `boot` 分区
- Linux：`cp files /media/$USER/boot/`

---

### 步骤 5：ZCU102 首次启动

#### 5.1 设置启动模式

**ZCU102 Rev 1.0 板卡**：

- 设置 SW6 开关 [4:1] 为 `off, off, off, on`
- 参考图：![SW6 开关位置](https://www.xilinx.com/content/dam/xilinx/support/documents/boards_and_kits/zcu102/ug1182-zcu102-eval-bd.pdf)

#### 5.2 连接串口

**硬件连接**：

1. 插入 SD 卡
2. 连接 USB 转 UART 线缆到 PC
3. 连接电源
4. 打开电源开关

**软件配置**：

- 打开串口终端（Putty、TeraTerm 等）
- 选择 COM 端口（设备管理器查看）
- 波特率：115200
- 数据位：8，停止位：1，奇偶校验：无

#### 5.3 登录系统

**启动完成后显示**：

```
Xilinx Zynq MP First Stage Boot Loader
Release 2022.2   Dec 15 2022  -  13:28:08
...
ZCU102 login:
```

**登录**：

- 用户名：`root`
- 密码：（空，直接回车）

#### 5.4 扩容 root 分区

**为什么要扩容？**

默认 root 分区只有几百 MB，不够用。

**扩容步骤**：

```bash
# 1. 拷贝扩容工具
cp /run/media/mmcblk0p1/dpu_sw_optimize.tar.gz ~

# 2. 解压
tar -xzf dpu_sw_optimize.tar.gz

# 3. 运行扩容脚本
cd dpu_sw_optimize
bash optimize_script.sh

# 4. 重启
reboot
```

---

### 步骤 6：编译 AI 模型

#### 6.1 下载 ResNet50 模型

**从 Model Zoo 下载**：

1. 访问：https://github.com/Xilinx/Vitis-AI/tree/master/model_zoo/model-list
2. 搜索 "resnet50"
3. 下载 `tf_resnetv1_50_imagenet_224_224_6.97G_3.0`
4. 解压

#### 6.2 准备 arch.json

**arch.json 是什么？**

描述 DPU 架构的文件，编译模型时需要。

**获取方法**：

从编译输出目录获取：`binary_container_1/sd_card/arch.json`

**或手动创建**：

```json
{
  "fingerprint": "0x101000056010200"
}
```

#### 6.3 编译模型

```bash
vai_c_tensorflow \
  --arch ./arch.json \
  -f quantized/quantized_baseline_6.96B_919.pb \
  --output_dir compile_result_zcu102 \
  -n tf_resnet50
```

**编译输出**：

在 `compile_result_zcu102` 目录生成 `tf_resnet50.xmodel`

**重命名**：

```bash
cd compile_result_zcu102
mv tf_resnet50.xmodel resnet50.xmodel
```

---

### 步骤 7：运行 Demo 验证

#### 7.1 拷贝模型到 ZCU102

**方法 1：通过 SD 卡**

1. 将 `resnet50.xmodel` 拷贝到 SD 卡 `boot` 分区
2. 将 SD 卡插回 ZCU102
3. 启动 ZCU102
4. 挂载 boot 分区：`mount /dev/mmcblk0p1 /run/media/mmcblk0p1`
5. 拷贝模型：`cp /run/media/mmcblk0p1/resnet50.xmodel ~`

**方法 2：通过网络**（如果 ZCU102 已联网）

```bash
# 在 ZCU102 上执行
scp user@host:/path/to/resnet50.xmodel ~
```

#### 7.2 运行推理

```bash
# 设置环境变量
export LD_LIBRARY_PATH=samples/lib
export XILINX_VART_FIRMWARE=/run/media/mmcblk0p1/dpu.xclbin

# 运行 ResNet50 推理
samples/bin/resnet50 img/bellpepper-994958.JPEG
```

#### 7.3 预期输出

```
Image: img/bellpepper-994958.JPEG
Top 5 predictions:
1. bell pepper (class 945): 0.9876
2. cucumber (class 920): 0.0089
3. zucchini (class 951): 0.0023
...
Inference time: 12.34 ms
```

**恭喜！你已成功运行 AI 推理！🎉**

---

## 第四部分：常见问题解答

### Q1：我是新手，应该如何开始？

**建议学习路径**：

1. **第 1 天**：阅读本入门指南，理解基础概念
2. **第 2-3 天**：安装 Vitis、Vitis AI、XRT 等工具
3. **第 4-5 天**：按照完整教程操作，完成首次部署
4. **第 6-7 天**：尝试修改 DPU 配置，理解不同架构的区别
5. **第 2 周**：尝试部署自己的 AI 模型

**关键点**：

- 不要急于求成，先理解概念再动手
- 遇到问题先查文档，再搜社区，最后问人
- 记录每一步操作，方便回滚和复盘

### Q2：编译时提示 "内存不足" 怎么办？

**原因**：

硬件编译需要大量内存（建议 32GB），内存不足会导致编译失败。

**解决方案**：

**方案 1：添加交换空间**（推荐）

```bash
# 创建 32GB 交换文件
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**方案 2：使用 B512 架构**

B512 编译时间更短，内存需求更低。

**方案 3：升级硬件**

如果经常做 FPGA 开发，建议升级到 32GB 或 64GB 内存。

### Q3：ZCU102 启动后无法登录怎么办？

**现象**：

启动后显示登录界面，但输入 `root` 后无响应或提示密码错误。

**原因**：

- root 文件系统损坏
- SD 卡烧录不完整
- SD 卡质量差

**解决方案**：

1. **重新烧录 SD 卡**
   - 使用 Balena Etcher，不要使用 dd 命令（容易出错）
   - 烧录完成后验证 MD5

2. **更换 SD 卡**
   - 使用 Class 10 以上的高速卡
   - 推荐品牌：SanDisk、Samsung

3. **检查 SD 卡是否有坏块**

```bash
# Linux 下检查
fsck /dev/mmcblk0p2
```

### Q4：运行应用时提示 "指纹不匹配" 怎么办？

**错误信息**：

```
CHECK fingerprint fail! model_fingerprint 0x... is un-matched with actual dpu_fingerprint 0x...
```

**原因**：

模型是用其他 DPU 架构编译的，与当前 DPU 不匹配。

**解决方案**：

1. **确认当前 DPU 架构**
   - 查看 `dpu_conf.vh` 文件中的 `DPU_TARGET` 定义

2. **重新编译模型**
   - 使用与当前 DPU 架构匹配的 `arch.json`
   - 重新编译模型

3. **验证指纹**
   - 对比 `arch.json` 中的指纹和错误信息中的 `actual dpu_fingerprint`

### Q5：如何确认 DPU 是否正常工作？

**检查方法**：

**方法 1：查看内核日志**

```bash
dmesg | grep -i dpu
```

**正常输出**：

```
[    2.387117] ####### Dpu Loaded Successful ########
```

**方法 2：查看加载的内核模块**

```bash
lsmod | grep zocl
```

**正常输出**：

```
zocl                  122880  0
```

**方法 3：使用 xbutil 工具**

```bash
xbutil examine
```

**正常输出**：

```
Device: xilinx_zcu102_base_202220_1
...
```

### Q6：我想深入学习，有哪些资源推荐？

**官方文档**：

1. **Vitis Unified Software Platform Documentation**
   - https://docs.xilinx.com/r/en-US/ug1400-vitis-embedded

2. **Vitis AI User Guide**
   - https://docs.xilinx.com/r/en-US/ug1414-vitis-ai

3. **ZCU102 Evaluation Board User Guide**
   - https://www.xilinx.com/support/documentation/boards_and_kits/zcu102/ug1182-zcu102-eval-bd.pdf

**社区资源**：

1. **Xilinx Vitis AI 论坛**
   - https://support.xilinx.com/s/topic/0TO2E000000YKY9WAO/vitis-ai-ai

2. **Vitis AI Github**
   - https://github.com/Xilinx/Vitis-AI

3. **Xilinx Vitis Tutorials**
   - https://github.com/Xilinx/Vitis-Tutorials

**视频教程**：

- Xilinx 官方 YouTube 频道：https://www.youtube.com/c/XilinxInc

---

## 第五部分：学习资源推荐

### 5.1 推荐学习路径

#### 第 1 阶段：基础入门（1-2 周）

**目标**：理解基本概念，完成首次部署

**学习材料**：

1. 本入门指南（必读）
2. 《ZCU102_Vitis_DPU_TRD_完整教程.md》（必做）
3. Xilinx 官方 Vitis AI 快速入门视频（YouTube）

**练习项目**：

- 完成 ZCU102 Vitis DPU TRD 教程
- 运行 ResNet50 推理 demo
- 修改 DPU 架构为 B1024，重新编译

#### 第 2 阶段：进阶学习（2-4 周）

**目标**：理解 DPU 架构，尝试自定义模型

**学习材料**：

1. DPU IP 产品指南（PG338）
2. Vitis AI 优化指南
3. Vitis 平台创建教程

**练习项目**：

- 部署自己的 AI 模型（YOLO、MobileNet 等）
- 创建自定义 Vitis 平台
- 优化 DPU 性能（调整架构参数）

#### 第 3 阶段：高级应用（1-2 个月）

**目标**：掌握完整开发流程，能够独立开发

**学习材料**：

1. Vitis HLS 编程指南
2. Vitis 加速库文档
3. Xilinx 应用笔记（Application Notes）

**练习项目**：

- 设计自定义 IP 核并集成到 DPU 系统
- 开发多模型流水线（例如：检测 + 分类）
- 优化系统性能（吞吐量、延迟）

### 5.2 推荐书籍

| 书名 | 作者 | 适合阶段 | 链接 |
|------|------|----------|------|
| 《Xilinx FPGA 权威设计指南》 | 何宾 | 入门 | - |
| 《嵌入式系统软硬件协同设计实战》 | 陈桂林 | 进阶 | - |
| 《Vitis High-Level Synthesis User Guide》 | Xilinx | 高级 | [在线阅读](https://docs.xilinx.com/r/en-US/ug1399-vitis-hls) |

### 5.3 在线课程

1. **Xilinx Adaptive Computing Developer Hub**
   - https://developer.xilinx.com/
   - 免费课程，包含 Vitis、Vitis AI 等

2. **Coursera - FPGA Computing Systems**
   - https://www.coursera.org/learn/fpga-computing-systems
   - 付费课程，深入讲解 FPGA 计算系统

3. **Udemy - Xilinx Vitis HLS 课程**
   - 搜索 "Xilinx Vitis HLS"
   - 付费课程，实战导向

---

## 附录：术语表

### A. 常用缩写

| 缩写 | 全称 | 中文 | 说明 |
|------|------|------|------|
| **AI** | Artificial Intelligence | 人工智能 | - |
| **DPU** | Deep Learning Processing Unit | 深度学习处理单元 | FPGA 上的 AI 加速器 |
| **FPGA** | Field Programmable Gate Array | 现场可编程门阵列 | 可编程硬件 |
| **XRT** | Xilinx Runtime | Xilinx 运行时 | 硬件加速运行时库 |
| **HLS** | High-Level Synthesis | 高级综合 | C/C++ → RTL |
| **PL** | Programmable Logic | 可编程逻辑 | FPGA 部分 |
| **PS** | Processing System | 处理系统 | ARM 处理器部分 |
| **MPSoC** | Multi-Processor System on Chip | 多处理器片上系统 | Zynq 架构 |
| **BSP** | Board Support Package | 板级支持包 | 硬件抽象层 |
| **CPUs** | Central Processing Unit | 中央处理器 | ARM Cortex-A53 |
| **DDR** | Double Data Rate | 双倍数据速率 | 内存类型 |

### B. 技术术语

#### B.1 硬件相关

| 术语 | 说明 |
|------|------|
| **Overlay** | 硬件设计文件，包含 DPU IP，编译后生成 .xclbin |
| **Bitstream** | 比特流文件，包含 FPGA 配置信息（.bit） |
| **XSA** | Xilinx Shell Archive，Vivado 导出的硬件平台文件 |
| **XPfM** | Vitis 平台文件，描述硬件和软件配置 |
| **AXI** | Advanced eXtensible Interface，ARM 总线协议 |
| **Clock Domain** | 时钟域，不同时钟频率的逻辑区域 |
| **Interrupt** | 中断，硬件通知 CPU 事件的机制 |

#### B.2 软件相关

| 术语 | 说明 |
|------|------|
| **VART** | Vitis AI Runtime，运行时库，应用调用 DPU 的 API |
| **XModel** | Vitis AI 编译生成的模型文件，DPU 可执行 |
| **Fingerprint** | 指纹，标识 DPU 架构的唯一 ID |
| **Quantization** | 量化，浮点模型 → 定点模型（FP32 → INT8） |
| **Compilation** | 编译，模型 → DPU 指令 |
| **Optimization** | 优化，提升模型性能的过程 |

#### B.3 流程相关

| 术语 | 说明 |
|------|------|
| **TRD** | Target Reference Design，目标参考设计 |
| **Common Image** | 通用镜像，PetaLinux 生成的标准 Linux 镜像 |
| **PetaLinux** | Xilinx 嵌入式 Linux 开发工具 |
| **SD Card Image** | SD 卡镜像，包含完整系统的镜像文件 |
| **Boot Mode** | 启动模式，ZCU102 支持 JTAG、QSPI、SD、NAND 等 |

---

## 总结

恭喜你完成了这份入门指南的学习！

### 你已经了解了

✅ ZCU102 开发板的基本概念  
✅ Vitis、Vitis AI、DPU 的作用和关系  
✅ 从零到成功运行 AI 推理的完整流程  
✅ 常见问题的解决方法  
✅ 进一步学习的资源和建议  

### 下一步行动

1. **立即行动**：按照《ZCU102_Vitis_DPU_TRD_完整教程.md》实际操作一遍
2. **遇到问题**：先查本指南第四部分，或搜索社区
3. **深入学习**：按照第五部分的学习路径继续进阶

### 获取帮助

- **官方论坛**：https://support.xilinx.com/s/topic/0TO2E000000YKY9WAO/vitis-ai-ai
- **Github Issues**：https://github.com/Xilinx/Vitis-AI/issues
- **本教程完整版**：《ZCU102_Vitis_DPU_TRD_完整教程.md》

---

**文档版本**：v1.0  
**最后更新**：2026 年 6 月 3 日  
**作者**：基于 Hackster.io 教程整理，专为入门者改编  
**反馈**：如有问题或建议，欢迎在 Github 提交 Issue
