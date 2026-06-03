# 阶段 10：商业项目实战——智能交通路口感知平台

## 学习目标

- 综合运用前 9 个阶段所有技能，完成端到端商业项目
- 理解 AI 推理 + 实时控制 + 云端上报的全栈集成
- 掌握工厂量产测试和 OTA 升级流程
- 建立完整的系统调试与性能优化方法论

---

## 10.1 项目架构回顾

```
┌─────────────────────────────────────────────────────────────┐
│                    ZCU102 EdgeVision-T1                      │
│                                                             │
│  摄像头 (MIPI CSI-2 4-lane)                                  │
│      │ V4L2 DMABUF                                         │
│      ▼                                                     │
│  YOLOv8s (DPU B4096, 8 FPS @ 640×640)                     │
│      │ 检测框 + 置信度                                       │
│      ▼                                                     │
│  ByteTrack 跟踪 (A53 Core 0, ~5ms/帧)                      │
│      │ 轨迹 + 速度向量                                       │
│      ▼                                                     │
│  事件检测 (闯红灯/违停/拥堵)                                   │
│      │ 事件列表                                             │
│      ▼                              A53 ←──RPMsg──→ R5     │
│  MQTT 上报 (TLS, 10s 周期)          心跳/队列数据   信号灯FSM │
│  gRPC 管理服务                                  Webster自适应 │
│  SQLite 离线缓存                                CAN 0x101帧  │
└─────────────────────────────────────────────────────────────┘
         ↓ TLS 1.3 / MQTT 5.0
┌──────────────────────────────┐
│  云端管理平台                  │
│  (Prometheus + Grafana)      │
└──────────────────────────────┘
```

---

## 10.2 复现路径（分阶段）

### Step 1：仿真验证（无硬件，1天）

```bash
cd 案例-智能交通路口感知平台
sudo bash scripts/setup_sim_env.sh
python3 tests/e2e_integration.py -v  # 22个测试全部通过
python3 sim/traffic_sim.py --frames 600 --fast
```

预期结果：
```
frames_processed: 600
effective_fps:    ~90
phase_changes:    ≥6
✓ 全部通过
```

### Step 2：Vivado 硬件设计（3天）

1. 创建 Block Design（参考阶段2）
2. 添加 DPU B4096 IP（参考 PG338）
3. 配置 MIPI CSI-2 接收链路
4. 添加 AXI CAN、ILA 探针
5. 生成比特流 + XSA

```bash
# 使用预制 Tcl 脚本
vivado -mode batch -source hardware/vivado_project/build_system.tcl
```

### Step 3：PetaLinux 构建（1天）

```bash
cd software/petalinux
petalinux-create --type project --template zynqMP --name edge_vision
petalinux-config --get-hw-description=../../hardware/vivado_project/zcu102_edge.xsa
petalinux-config -c rootfs  # 添加 opencv, vitis-ai-library
petalinux-build
petalinux-package --boot --fsbl --u-boot --pmufw --fpga --force
```

### Step 4：AI 模型部署（1天）

```bash
# Docker 量化（需要 GPU 服务器）
docker run --gpus all -v $(pwd):/workspace xilinx/vitis-ai-gpu:latest \
    python3 /workspace/ai/quantization/quantize_yolov8.py

# 板卡编译
vai_c_xir \
    --xmodel ai/models/yolov8s_traffic_float.xmodel \
    --arch /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json \
    --net_name traffic_yolov8 \
    --output_dir ai/deploy/
```

### Step 5：C++ 应用编译（1天）

```bash
# 交叉编译
source /opt/petalinux-2023.1/sdk/environment-setup-aarch64-xilinx-linux
cd software/app
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DSIM_MODE=OFF
make -j4
```

### Step 6：板卡集成测试（1天）

```bash
# 烧录 SD 卡，登录到 ZCU102
ssh root@192.168.1.100

# 运行工厂测试脚本
python3 scripts/factory_test.py 192.168.1.100 edge001

# 运行主应用
./traffic_edge --channels 1 --mqtt mqtt.broker.com --device-id edge001
```

### Step 7：性能优化（按需）

| 优化目标 | 手段 | 预期提升 |
|----------|------|----------|
| DPU 吞吐 | 双 DPU 实例并发推理 | 15 FPS → 8 FPS（每路） |
| 内存带宽 | 分配 HP0+HP1 给 DPU | 减少拥塞 |
| 跟踪延迟 | NEON 优化 IoU 矩阵 | 5ms → 2ms |
| 网络延迟 | MQTT QoS=1 + 批量上报 | 减少连接开销 |

---

## 10.3 关键性能指标（KPI）

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 端到端延迟 | <200ms（摄像头→事件上报）| 时间戳打点 |
| 检测 FPS | ≥8 fps（640×640 YOLOv8s）| dpu_runner_benchmark |
| 跟踪精度 | MOTA ≥ 70% | MOT 评估工具 |
| CAN 帧延迟 | <10ms（相位切换→发帧）| ILA 抓取 |
| MQTT 上报 | 10s 周期，丢包率<0.1%| 长时间运行统计 |
| 系统功耗 | <25W（核心板）| 功率计测量 |
| MTBF | >10000h | 加速老化测试 |

---

## 10.4 工厂测试清单

```python
# scripts/factory_test.py 测试项目：
TEST_ITEMS = [
    "T01_board_power_on",         # 上电检测
    "T02_ddr_memtest",            # DDR 读写测试
    "T03_emmc_read_write",        # eMMC 读写速度
    "T04_eth_loopback",           # GbE 自环测试
    "T05_can_loopback",           # CAN 自环（需要CAN收发器）
    "T06_usb_detect",             # USB 设备检测
    "T07_fpga_bitstream_load",    # 比特流加载验证
    "T08_dpu_inference",          # DPU 推理正确性（黄金参考）
    "T09_camera_capture",         # 摄像头抓帧（需接摄像头）
    "T10_mqtt_connect",           # MQTT 连接测试
    "T11_rpmsg_loopback",         # A53-R5 通信自环
    "T12_temperature_check",      # 温度传感器读取
]
```

---

## 10.5 学习路径总结

完成本项目后，你已掌握：

| 技术域 | 技能 | 就业方向 |
|--------|------|----------|
| FPGA 设计 | Vivado IPI、时序约束、HLS | FPGA 工程师 |
| 嵌入式 Linux | PetaLinux、驱动开发、V4L2 | 嵌入式 Linux 工程师 |
| AI 部署 | Vitis AI、PTQ量化、VART | AI 部署工程师 |
| 实时控制 | FreeRTOS、OpenAMP、TCM | RTOS 工程师 |
| 高速接口 | GTH、MIPI、CAN | 硬件工程师 |
| 系统集成 | ILA调试、性能分析、OTA | 系统工程师 |
| 云端连接 | MQTT/TLS、gRPC、Docker | IoT 全栈工程师 |

---

## 参考资源

| 资源 | 说明 |
|------|------|
| [项目主目录](../../案例-智能交通路口感知平台/) | 完整项目代码 |
| [仿真验证指南](../../案例-智能交通路口感知平台/docs/仿真验证指南.md) | 无硬件验证指南 |
| [参考资源整理](../../案例-智能交通路口感知平台/docs/参考资源整理.md) | 官方文档索引 |
| [网站交互演示](../../案例-智能交通路口感知平台/website/) | 可视化流程展示 |
