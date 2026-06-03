/**
 * EdgeVision-T1 网站数据层
 * 商业闭环流程 · 技术模块 · 技能矩阵 · 官方文档资源
 */

// ═══════════════════════════════════════════════════════════
// 商业闭环流程（9个阶段）
// ═══════════════════════════════════════════════════════════
const FLOW_PHASES = [
  {
    id: 'req',
    phase: '01',
    title: '需求与立项',
    icon: '📋',
    color: '#00D4FF',
    duration: '2周',
    deliverable: 'PRD文档',
    desc: '明确商业目标，技术可行性论证，项目立项',
    details: {
      overview: '从市场调研到技术方案，确立项目边界与商业价值。',
      tasks: [
        '市场调研：智能交通行业规模、竞品分析、客户访谈',
        '性能指标定义：4K×4路、<22ms延迟、<10ms信号响应',
        '带宽计算：4×(3840×2160×30fps×12bit) = 5.97 GB/s 原始数据',
        '技术可行性：ZCU102资源评估，DPU B4096算力核算',
        '商业模型选型：硬件销售 / 硬件+SaaS / 整体解决方案',
        '风险矩阵：技术风险R1-R8，量产风险M1-M4'
      ],
      kpis: [
        { label: '检测准确率', value: '≥ 92% mAP50' },
        { label: '推理延迟', value: '< 22 ms' },
        { label: '信号响应', value: '< 10 ms' },
        { label: '系统稳定性', value: '99.9% 在线率' },
        { label: '工作温度', value: '-40°C ~ +75°C' }
      ],
      tools: ['Axure RP（PRD）', 'Excel（BOM估算）', 'Miro（系统框图）'],
      code: `# 带宽需求速算
cameras    = 4
width, height, fps = 3840, 2160, 30
bits_per_pixel = 12          # RAW12 Bayer
raw_bw_GBs = cameras * width * height * fps * bits_per_pixel / 8 / 1e9
# → 5.97 GB/s  → 压缩后 NV12 ≈ 1.99 GB/s，DDR4 带宽 38.4 GB/s 充裕`
    }
  },
  {
    id: 'arch',
    phase: '02',
    title: '系统架构设计',
    icon: '🏗️',
    color: '#7B61FF',
    duration: '2周',
    deliverable: '架构文档+DDR映射',
    desc: 'PS/PL功能划分，存储映射，接口协议定义',
    details: {
      overview: '确立异构多核协同架构，零拷贝数据通路，三核并行策略。',
      tasks: [
        'PL负责：4路MIPI接收 · ISP · DPU · OSD · 10GbE MAC · AXI CAN',
        'A53负责：Linux主应用 · AI应用层 · MQTT/gRPC · OTA',
        'R5负责：FreeRTOS实时控制 · 信号灯FSM · CAN发送',
        'DDR4内存映射：视频缓冲区 / DPU工作区 / RPMsg共享内存',
        'AXI总线矩阵：HP0-3分配，HPC0挂载DPU，GP0/1挂载控制寄存器',
        '时钟树设计：FCLK0 250MHz(ISP) / FCLK1 300MHz(DPU) / FCLK2 150MHz(AXI)'
      ],
      kpis: [
        { label: 'DDR4带宽', value: '38.4 GB/s' },
        { label: 'FCLK0', value: '250 MHz (ISP)' },
        { label: 'FCLK1', value: '300 MHz (DPU)' },
        { label: 'AXI HP口', value: '4个 @ 128bit' },
        { label: 'PL资源利用', value: '~75%' }
      ],
      tools: ['draw.io（架构图）', 'Excel（内存映射）', 'Xilinx Power Estimator'],
      code: `/* DDR4 内存映射 */
0x0000_0000 - 0x7FFF_FFFF  Linux 内核 + 应用（2 GB）
0x8000_0000 - 0x8BFF_FFFF  视频帧缓冲区（4路 × 3帧 × NV12 = 192 MB）
0x8C00_0000 - 0xB7FF_FFFF  DPU 工作内存（704 MB）
0xB800_0000 - 0xBFFF_FFFF  RPMsg 共享内存（128 MB，与 R5 共享）
0xC000_0000 - 0xFFFF_FFFF  R5 FreeRTOS 私有堆（1 GB）`
    }
  },
  {
    id: 'fpga',
    phase: '03',
    title: 'FPGA/PL 硬件开发',
    icon: '⬡',
    color: '#FF6B35',
    duration: '6周',
    deliverable: 'XSA + 比特流',
    desc: 'Vivado BD设计，HLS IP核，时序收敛，资源优化',
    details: {
      overview: '以Vivado Block Design为核心，集成MIPI、ISP HLS IP、DPU B4096、10GbE等所有PL功能。',
      tasks: [
        'Vivado Block Design：Zynq PS配置 + 所有IP互联',
        'HLS ISP Pipeline：Bayer去马赛克 → 白平衡 → Gamma → NV12转换（DATAFLOW）',
        'HLS OSD Overlay：在线字符叠加，帧率/检测框渲染，II=1流水',
        'DPU B4096集成：pg338-dpu IP核，AXI HP0连接',
        'XXV Ethernet IP：25G MAC，GTH收发器，10GbE实际链速',
        'AXI CAN集成：500Kbps，信号灯控制器通信',
        '时序约束：XDC文件，CDC路径set_max_delay，Pblock约束',
        '实现：7轮timing closure，WNS ≥ 0'
      ],
      kpis: [
        { label: 'LUT利用率', value: '188K / 274K (69%)' },
        { label: 'BRAM', value: '364 / 912 (40%)' },
        { label: 'DSP', value: '1120 / 2520 (44%)' },
        { label: 'ISP时钟', value: '250 MHz 收敛' },
        { label: 'DPU时钟', value: '300 MHz 收敛' }
      ],
      tools: ['Vivado 2023.1', 'Vitis HLS 2023.1', 'ChipScope/ILA', 'Xilinx Power Estimator'],
      code: `// HLS ISP 顶层 DATAFLOW
void isp_pipeline(AXIS_IN& s_axis, AXIS_OUT& m_axis,
                  uint16_t blk, uint16_t wb_r, uint16_t wb_g, uint16_t wb_b,
                  uint8_t bayer) {
#pragma HLS INTERFACE axis port=s_axis
#pragma HLS INTERFACE axis port=m_axis
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL
#pragma HLS DATAFLOW
  // 7级流水：RAW → BLC → WB → Demosaic → Gamma → CCM → NV12
  hls::Mat<H4K,W4K,HLS_16UC1> raw, blc_out, wb_out;
  hls::Mat<H4K,W4K,HLS_8UC3>  rgb, gamma_out, ccm_out;
  hls::Mat<H4K,W4K,HLS_8UC1>  nv12_y, nv12_uv;
  blc_correction(s_axis, raw, blk);
  white_balance(raw, wb_out, wb_r, wb_g, wb_b);
  // ...
}`
    }
  },
  {
    id: 'ai',
    phase: '04',
    title: 'AI模型开发与部署',
    icon: '🧠',
    color: '#00FF88',
    duration: '4周',
    deliverable: 'xmodel量化模型',
    desc: 'YOLOv8训练→量化→DPU部署，LPRNet车牌识别',
    details: {
      overview: '数据集准备→模型训练→PTQ量化→DPU编译→VART推理，全链路AI开发流程。',
      tasks: [
        '数据集：UA-DETRAC + 私有标注，~50K帧，含恶劣天气增强',
        'YOLOv8s训练：AdamW，300 epochs，mAP50=88.5%，ONNX导出',
        'Vitis AI PTQ量化：CalibDataset 1000张，INT8，精度损失<1%',
        'vai_c_xir编译：针对DPU B4096(ZCU102) arch.json编译xmodel',
        'VART推理：vart::Runner，批量推理，延迟<18ms/帧',
        'LPRNet车牌识别：CTC解码，96×24输入，68类字符集',
        'ByteTrack多目标跟踪：IoU匹配+Re-ID，实现虚拟线计数',
        '推理引擎集成：多线程C++，SCHED_FIFO调度'
      ],
      kpis: [
        { label: 'YOLOv8s mAP50', value: '88.5%' },
        { label: 'DPU推理延迟', value: '< 18 ms/帧' },
        { label: '量化精度损失', value: '< 1%' },
        { label: '车牌识别率', value: '≥ 95%' },
        { label: '跟踪MOTA', value: '≥ 78%' }
      ],
      tools: ['PyTorch 2.x', 'Vitis AI 3.5', 'vai_q_pytorch', 'vai_c_xir', 'ONNX Runtime'],
      code: `# PTQ量化三阶段
# Phase 1: 校准
quantizer = torch_quantizer('calib', model, input_args, quant_config_file)
calib_model = quantizer.quant_model
for data, _ in calib_loader:
    calib_model(data)
quantizer.export_quant_config()

# Phase 2: 测试精度
quantizer = torch_quantizer('test', model, input_args, quant_config_file)
test_acc = evaluate(quantizer.quant_model, val_loader)

# Phase 3: 导出xmodel
quantizer.export_xmodel(output_dir='./quantized')
# vai_c_xir 编译
os.system("vai_c_xir -x quantized/YoloV8s_int.xmodel "
          "-a /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json "
          "-o ./deploy -n traffic_yolov8")`
    }
  },
  {
    id: 'sw',
    phase: '05',
    title: '嵌入式软件开发',
    icon: '🐧',
    color: '#FFD700',
    duration: '5周',
    deliverable: 'PetaLinux镜像+应用',
    desc: 'PetaLinux BSP，Linux驱动，多线程C++应用，gRPC服务',
    details: {
      overview: 'PetaLinux构建定制Linux系统，V4L2视频驱动，零拷贝帧管理，MQTT/gRPC通信栈。',
      tasks: [
        'PetaLinux项目创建：petalinux-create -t project --template zynqMP',
        '内核配置：V4L2_VIDEO_DEV, VIDEOBUF2_DMABUF, CONFIG_CAN, OpenAMP',
        '设备树：MIPI CSI2, AXI VDMA, AXI CAN, reserved-memory, rpmsg',
        'V4L2驱动：platform_driver, vb2_queue_init, DMABUF零拷贝',
        '帧管理器：/dev/mem mmap物理地址，VideoFrame零拷贝，lazy BGR转换',
        '推理引擎：VART vart::Runner，LPR两段式推理，ByteTrack集成',
        '事件检测：虚拟线闯红灯检测，逆行/违停，拥堵判断',
        'gRPC服务：15个RPC，StreamDetections流式推送，OTA进度上报',
        'MQTT/TLS：双向证书，主题树schema，SQLite离线缓存'
      ],
      kpis: [
        { label: '启动时间', value: '< 12 s (冷启)' },
        { label: 'A53 CPU占用', value: '< 60%' },
        { label: '内存占用', value: '< 1.5 GB' },
        { label: 'gRPC延迟', value: '< 5 ms' },
        { label: '捕获帧率', value: '30 FPS × 4路' }
      ],
      tools: ['PetaLinux 2023.1', 'CMake 3.24', 'gRPC C++ 1.54', 'Mosquitto 2.x', 'SQLite 3'],
      code: `// 帧管理器零拷贝访问
FrameManager::FrameManager() {
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    // 映射 PL VDMA 写入的 DDR4 物理地址
    base_ptr_ = mmap(nullptr, TOTAL_BUF_SIZE,
                     PROT_READ | PROT_WRITE, MAP_SHARED, fd,
                     VIDEO_BUF_PHYS_BASE);   // 0x80000000
    // VideoFrame 直接持有 NV12 裸指针，无拷贝
}
// VART 推理
auto runner = vart::Runner::create_runner(graph->get_root_subgraph(), "run");
auto inputs  = runner->get_inputs();
auto outputs = runner->get_outputs();
inputs[0]->copy_from_host(nv12_data.data(), nv12_data.size());
auto job = runner->execute_async(inputs, outputs);
runner->wait(job.first, -1);  // 阻塞等待 DPU 完成`
    }
  },
  {
    id: 'rtos',
    phase: '06',
    title: '实时控制开发',
    icon: '⚡',
    color: '#FF4088',
    duration: '3周',
    deliverable: 'R5 FreeRTOS固件',
    desc: 'FreeRTOS信号灯FSM，CAN通信，OpenAMP与A53协同',
    details: {
      overview: 'R5@500MHz运行FreeRTOS，实现<10ms信号灯响应，自适应Webster配时算法。',
      tasks: [
        'FreeRTOS任务规划：5个任务，优先级WDT=5>CAN=4>FSM=3>OpenAMP=2>Tel=1',
        '信号灯FSM：10个相位，PHASE_ALLRED隔离，Webster自适应算法',
        'CAN驱动：AXI CAN IP，500Kbps，ISR接收控制命令',
        'OpenAMP/RPMsg：A53发送队列长度→R5调整配时，心跳监测',
        '链接脚本：ATCM 64KB存放中断向量+ISR，TCM零等待延迟',
        '看门狗：硬件WDT，超时自动复位，故障安全模式',
        '安全模式：A53失联>30s自动切换本地固定时序'
      ],
      kpis: [
        { label: '信号响应时间', value: '< 10 ms' },
        { label: 'CAN帧延迟', value: '< 2 ms' },
        { label: 'FSM任务周期', value: '100 ms' },
        { label: 'WDT超时', value: '500 ms' },
        { label: 'OpenAMP延迟', value: '< 5 ms' }
      ],
      tools: ['FreeRTOS v10.5', 'Xilinx BSP', 'OpenAMP 2023.1', 'Vitis IDE', 'XSCT'],
      code: `/* 自适应 Webster 算法（简化版）*/
static uint32_t webster_cycle(const SignalFSM_t *fsm) {
    float total_flow = 0;
    for (int i = 0; i < 4; i++)
        total_flow += fsm->queue_len[i] * SATURATION_FLOW;
    float lost_time = PHASE_COUNT * PHASE_LOST_TIME_S;
    float y_sum     = total_flow / SATURATION_FLOW;
    // Webster公式：C = (1.5L + 5) / (1 - Y)
    float C = (1.5f * lost_time + 5.0f) / (1.0f - y_sum);
    uint32_t cycle_s = (uint32_t)CLAMP(C, MIN_CYCLE_S, MAX_CYCLE_S);
    return cycle_s;
}
// CAN帧发送（ID=0x101，控制信号灯控制器）
frame.id  = 0x101;
frame.dlc = 4;
frame.data[0] = current_phase;
frame.data[1] = remain_s;
frame.data[2] = (flags >> 8) & 0xFF;
frame.data[3] = flags & 0xFF;`
    }
  },
  {
    id: 'integration',
    phase: '07',
    title: '系统集成与测试',
    icon: '🔗',
    color: '#00D4FF',
    duration: '3周',
    deliverable: '测试报告+DVT签核',
    desc: '软硬件联调，性能测试，稳定性验证，DVT签核',
    details: {
      overview: '全系统集成测试，端到端延迟验证，72小时稳定性烤机，DVT报告。',
      tasks: [
        'HIL测试：Hardware-in-Loop，模拟4路摄像头输入',
        '端到端延迟：从像素到信号灯响应 <32ms 全链路验证',
        'AI精度回归：现场数据集重测，mAP50 ≥ 88%',
        '压力测试：72小时连续运行，温度/内存/CPU监控',
        '网络故障注入：断网→SQLite缓存→重连上报验证',
        '看门狗测试：强制R5挂死，验证<500ms自动复位',
        'OTA升级测试：A/B分区切换，断电恢复验证',
        '工厂测试脚本：factory_test.py，9项自动化测试'
      ],
      kpis: [
        { label: '端到端延迟', value: '< 32 ms' },
        { label: '72h稳定运行', value: '0次异常重启' },
        { label: '功耗', value: '< 25 W (满负荷)' },
        { label: 'OTA成功率', value: '> 99.5%' },
        { label: 'FCT通过率', value: '> 98%' }
      ],
      tools: ['pytest', 'iperf3', 'can-utils', 'Valgrind', 'perf', 'factory_test.py'],
      code: `# 工厂测试脚本（factory_test.py）
runner = FactoryTestRunner(device_ip, device_id)
runner.connect()

tests = [
    ('Linux启动验证',   runner.test_linux_boot),
    ('DPU驱动检测',    runner.test_dpu_available),
    ('4路摄像头检测',  runner.test_cameras),
    ('DPU推理精度',   runner.test_dpu_inference),
    ('10GbE回环',    runner.test_10gbe_loopback),
    ('CAN总线回环',   runner.test_can_loopback),
    ('温度传感器',    runner.test_temperature_sensors),
    ('固件版本',     runner.test_flash_firmware_version),
    ('安全启动',     runner.test_secure_boot),
]
# 结果上传 MES 系统，生成 JSON 报告`
    }
  },
  {
    id: 'secure',
    phase: '08',
    title: '安全与量产',
    icon: '🔒',
    color: '#FF8C00',
    duration: '2周',
    deliverable: '量产包+eFUSE规范',
    desc: '安全启动链，eFUSE编程，量产自动化，CE/FCC认证',
    details: {
      overview: '从BootROM到应用的完整信任链，AES-256比特流加密，RSA-4096签名，量产自动化。',
      tasks: [
        '安全启动链：BootROM→FSBL(RSA验证)→U-Boot→Linux IMA完整性度量',
        'eFUSE编程：RSA公钥哈希烧录，JTAG禁用，密码登录禁用',
        'AES-256比特流加密：BBRAM存储密钥，每批次唯一密钥',
        '量产烧录工具：自动化FSBL+bitstream+rootfs烧录',
        '固件版本管理：/etc/traffic_edge_version，BUILD_ID对应',
        'SWUpdate A/B：eMMC分区表，bootcount自动回滚',
        '认证：CE/FCC EMC测试，工业温度级-40~75°C测试',
        'BOM成本：$486元器件+$80组装=$566（1000台单价）'
      ],
      kpis: [
        { label: 'RSA密钥长度', value: '4096 bit' },
        { label: 'AES加密', value: '256 bit CBC' },
        { label: 'eFUSE烧录', value: '< 30 s/台' },
        { label: '量产节拍', value: '< 8 min/台（含测试）' },
        { label: 'OTA包大小', value: '< 300 MB' }
      ],
      tools: ['Xilinx HSM', 'SWUpdate 2023.02', 'bootgen', 'mkimage', 'openssl'],
      code: `# 安全启动链验证
# 1. eFUSE 状态检查
xsdb% connect
xsdb% targets -set -filter {name =~ "PSU"}
xsdb% rrd efuse_sec_ctrl

# 2. 比特流 AES 加密（bootgen）
# bif 文件指定加密密钥
the_ROM_image: { [aeskeyfile] device.nky [encryption=aes] system.bit }
bootgen -image encrypt.bif -arch zynqmp -o encrypted.bit

# 3. IMA 度量日志验证
cat /sys/kernel/security/ima/ascii_runtime_measurements | head -5`
    }
  },
  {
    id: 'ops',
    phase: '09',
    title: '商业运营',
    icon: '📈',
    color: '#7B61FF',
    duration: '持续',
    deliverable: '云端SaaS平台',
    desc: '云端运维，OTA升级，数据变现，商业模式迭代',
    details: {
      overview: '量产交付后，通过SaaS平台实现持续盈利：运维、数据服务、算法迭代。',
      tasks: [
        '云端管理平台：设备在线状态，远程诊断，配置下发',
        'OTA升级服务：灰度发布，A/B回滚，进度可视化',
        '数据分析报告：交通流量统计，拥堵预测，违规热力图',
        '算法持续迭代：新场景数据回流，模型在线更新',
        '客户SLA：99.9%在线率SLA，4小时响应协议',
        '扩展商机：停车场版本，高速公路版本，大型园区版本',
        '三年盈利预测：1000台×$566成本，卖$2200+$80/月SaaS'
      ],
      kpis: [
        { label: '设备售价', value: '$2,200 / 台' },
        { label: 'SaaS月费', value: '$80 / 台 / 月' },
        { label: '毛利率', value: '≥ 60%' },
        { label: '回本周期', value: '< 18 个月' },
        { label: '市场规模', value: '¥800亿（国内）' }
      ],
      tools: ['Kubernetes', 'Prometheus+Grafana', 'MQTT Broker', 'PostgreSQL', 'Airflow'],
      code: `# MQTT 数据上报 Schema
Topic: traffic/edge/{city}/{district}/{device_id}/flow
Payload:
{
  "ts": 1700000000,
  "device_id": "edge001",
  "channel": 0,
  "interval_s": 60,
  "counts": {"car": 45, "truck": 8, "person": 12, "bus": 3},
  "queue_m": 25.3,
  "avg_speed_kph": 32.1,
  "occupancy_pct": 68.5
}`
    }
  }
];

// ═══════════════════════════════════════════════════════════
// 技术模块详解（五大技术层）
// ═══════════════════════════════════════════════════════════
const MODULE_DATA = {
  hw: {
    title: 'FPGA/PL 硬件层',
    subtitle: 'Vivado Block Design · Vitis HLS · XDC约束 · 时序收敛',
    cards: [
      {
        title: 'Vivado Block Design',
        icon: '🔧',
        level: 5,
        desc: '以图形化BD为核心，集成所有PL IP核。关键配置：Zynq PS AXI接口、4路MIPI RX SS、DPU B4096、XXV Ethernet、AXI CAN等18个IP。',
        tags: ['Vivado 2023.1', 'Block Design', 'IP Integrator', 'Tcl自动化'],
        detail: 'build.tcl 自动创建完整BD，一键从IP集成到比特流生成，支持CI/CD流程。'
      },
      {
        title: 'HLS ISP 流水线',
        icon: '📷',
        level: 5,
        desc: '7级DATAFLOW流水：RAW→BLC→白平衡→去马赛克→Gamma→CCM→NV12。4K@30fps×4路，单路25Mpix/s，II=1吞吐。',
        tags: ['Vitis HLS', 'DATAFLOW', 'AXI-Stream', '4K@30fps'],
        detail: '#pragma HLS DATAFLOW实现所有阶段并行，ARRAY_PARTITION优化LUT查找表访问。'
      },
      {
        title: 'DPU B4096 集成',
        icon: '🧮',
        level: 5,
        desc: 'Xilinx Deep Learning Processing Unit，4096 MAC单元，@300MHz提供2.5T OPS算力。通过AXI HP0连接DDR4，支持YOLOv8s INT8推理。',
        tags: ['DPU B4096', 'pg338', '2.5T OPS', 'INT8推理'],
        detail: 'Pblock约束在CLOCKREGION_X0Y3:X3Y4，避免与ISP区域时序干扰。'
      },
      {
        title: '10GbE GTH SerDes',
        icon: '🌐',
        level: 4,
        desc: 'XXV Ethernet IP + GTH收发器实现10GbE，156.25MHz参考时钟，实测吞吐>9.5Gbps，支持云端视频回传。',
        tags: ['XXV Ethernet', 'GTH', '10GbE', 'PG210'],
        detail: '使用loopback自测验证物理层，iperf3测试实际吞吐率>8Gbps即通过FCT。'
      },
      {
        title: 'HLS OSD 叠加',
        icon: '🖼️',
        level: 4,
        desc: '在线字符叠加IP，5×7位图字体，支持64个检测框同时渲染。class_id颜色编码，置信度/跟踪ID显示，II=1流水。',
        tags: ['HLS OSD', '5×7字体', '64框并行', 'AXI-Stream'],
        detail: 'CLASS_COLORS[8]数组用PP_BUFFER存储，避免LUT推断失败。'
      },
      {
        title: 'AXI总线架构',
        icon: '🚌',
        level: 5,
        desc: 'AXI4 HP0-3：视频DMA高带宽读写。AXI4-Lite GP0：控制寄存器访问。AXI4-Stream：流式视频数据通路。总带宽峰值>30GB/s。',
        tags: ['AXI4', 'AXI4-Lite', 'AXI4-Stream', 'SmartConnect'],
        detail: 'AXI SmartConnect 路由矩阵，4×128bit HP口，实测峰值带宽满足5.97GB/s需求。'
      }
    ]
  },
  ai: {
    title: 'AI 推理层',
    subtitle: 'YOLOv8 训练 · Vitis AI 量化 · DPU 部署 · ByteTrack 跟踪',
    cards: [
      {
        title: 'YOLOv8s 目标检测',
        icon: '👁️',
        level: 5,
        desc: '在UA-DETRAC+私有数据集上微调，6类（车/卡/公/骑/人/非机），mAP50=88.5%，ONNX导出→PTQ量化→DPU部署，推理<18ms/帧。',
        tags: ['YOLOv8s', 'PyTorch', 'ONNX', 'mAP50=88.5%'],
        detail: 'mosaic=1.0+mixup+copy_paste增强，close_mosaic=15最后阶段关闭防止震荡。'
      },
      {
        title: 'Vitis AI PTQ量化',
        icon: '⚡',
        level: 5,
        desc: '三阶段量化：校准→精度验证→xmodel导出。vai_c_xir编译针对ZCU102 DPU B4096架构，INT8精度损失<1%。',
        tags: ['Vitis AI 3.5', 'PTQ', 'INT8', 'xmodel'],
        detail: 'CalibDataset 1000张代表性图片，使用torch_quantizer进行逐层激活分析。'
      },
      {
        title: 'LPRNet 车牌识别',
        icon: '🚗',
        level: 4,
        desc: '轻量级车牌OCR网络，SmallBasicBlock分解卷积，CTC输出，68字符集（34省份+24字母+10数字），推理<3ms/张。',
        tags: ['LPRNet', 'CTC', '68字符类', '<3ms'],
        detail: '从车辆bbox裁剪下半60%区域，resize到96×24，两段式推理流水。'
      },
      {
        title: 'ByteTrack 多目标跟踪',
        icon: '🔄',
        level: 4,
        desc: 'IoU匹配+低置信度候选二次关联，保留轨迹30帧历史，虚拟计数线检测过车计数，MOTA≥78%。',
        tags: ['ByteTrack', 'IoU匹配', '轨迹管理', 'MOTA=78%'],
        detail: '虚拟线向量叉积判断穿越方向，区分正常/逆行；静止>30s判断违停。'
      },
      {
        title: 'VART 推理运行时',
        icon: '🚀',
        level: 5,
        desc: 'Vitis AI运行时，xir::Graph加载xmodel，vart::Runner管理DPU任务队列，异步执行，支持多DPU并行。',
        tags: ['VART', 'xir::Graph', 'vart::Runner', '异步执行'],
        detail: 'execute_async+wait模式，inference thread与capture thread解耦，最大化DPU利用率。'
      },
      {
        title: '事件检测引擎',
        icon: '🚨',
        level: 4,
        desc: '6类交通事件：闯红灯/逆行/违停/行人闯入/拥堵/超重车。基于轨迹分析+信号灯相位同步判断，毫秒级触发。',
        tags: ['事件检测', '闯红灯', '轨迹分析', '实时告警'],
        detail: 'EventDetector订阅信号灯相位状态，RED_LIGHT_VIOLATION需确认虚拟停止线穿越且信号为红。'
      }
    ]
  },
  linux: {
    title: '嵌入式 Linux 层',
    subtitle: 'PetaLinux 2023.1 · V4L2驱动 · 零拷贝帧管理 · 多线程应用',
    cards: [
      {
        title: 'PetaLinux 定制构建',
        icon: '🐧',
        level: 5,
        desc: 'Yocto-based嵌入式Linux，XSA导入→内核配置→rootfs裁剪→SDK生成。内核5.15，包含V4L2/DRM/OpenAMP/CAN驱动。',
        tags: ['PetaLinux 2023.1', 'Yocto', 'bitbake', 'SDK交叉编译'],
        detail: 'petalinux-config/kernel/rootfs分层配置，meta-user层添加自定义应用包和systemd服务。'
      },
      {
        title: 'V4L2 视频采集驱动',
        icon: '📹',
        level: 5,
        desc: 'platform_driver挂载AXI VDMA，vb2_queue_init初始化DMA缓冲队列，DMABUF零拷贝，NV12格式，1920×1080@30fps。',
        tags: ['V4L2', 'videobuf2', 'DMABUF', 'platform_driver'],
        detail: 'buf_queue()填写DMA地址到VDMA寄存器，ISR回调vb2_buffer_done()通知应用层。'
      },
      {
        title: '零拷贝帧管理器',
        icon: '💨',
        level: 5,
        desc: '/dev/mem mmap物理地址0x80000000，VideoFrame持有NV12裸指针，get_preview()懒加载BGR缩略图，无内存拷贝全链路。',
        tags: ['零拷贝', 'mmap', 'shared_ptr', '引用计数'],
        detail: 'ChannelBuffer三槽滚动，mark_ready()触发condition_variable通知推理线程，drop_count统计丢帧。'
      },
      {
        title: '设备树配置',
        icon: '🌳',
        level: 4,
        desc: '包含4路MIPI CSI2、AXI VDMA、AXI CAN、OpenAMP RPMsg、reserved-memory、IIO温度传感器等完整DT节点。',
        tags: ['设备树DTS', 'MIPI CSI2', 'OpenAMP', 'reserved-memory'],
        detail: 'reserved-memory节点no-map确保Linux不使用视频缓冲区和RPMsg共享内存区域。'
      },
      {
        title: '多线程应用架构',
        icon: '🧵',
        level: 5,
        desc: '6个线程：4×V4L2采集(SCHED_FIFO pri=80)+1×DPU推理(pri=70)+1×OpenAMP心跳。gRPC Server阻塞主线程。',
        tags: ['C++17', 'SCHED_FIFO', 'pthread', 'std::thread'],
        detail: 'pthread_setschedparam设置实时优先级，mlockall()锁定内存避免页面抖动影响实时性。'
      },
      {
        title: 'CMake 交叉编译',
        icon: '⚙️',
        level: 4,
        desc: 'PetaLinux SDK提供aarch64工具链，find_package集成OpenCV/gRPC/VART，-march=armv8-a -mtune=cortex-a53优化。',
        tags: ['CMake 3.24', 'AArch64', 'OpenCV 4.5', 'gRPC C++'],
        detail: '集成ASan调试构建，Release构建-O2 -DNDEBUG，生成独立可部署二进制。'
      }
    ]
  },
  rtos: {
    title: '实时控制层（FreeRTOS）',
    subtitle: 'Cortex-R5 · FreeRTOS v10.5 · 信号灯FSM · CAN总线 · OpenAMP',
    cards: [
      {
        title: 'FreeRTOS 任务调度',
        icon: '⚡',
        level: 4,
        desc: '5个任务，抢占式优先级调度：WDT喂狗(5)>CAN接收(4)>信号FSM(3)>OpenAMP通信(2)>遥测上报(1)，1ms时钟节拍。',
        tags: ['FreeRTOS v10.5', '抢占调度', '1ms时钟', '5任务'],
        detail: 'configUSE_TIME_SLICING=0关闭同优先级时间片，避免FSM被遥测任务抢占导致相位计时误差。'
      },
      {
        title: '信号灯状态机',
        icon: '🚦',
        level: 5,
        desc: '10个相位（NS绿/黄/红+EW绿/黄/红+左转相位+全红）的完整FSM，每100ms更新，<10ms CAN帧发送到信号控制器。',
        tags: ['FSM', 'CAN发送', '<10ms响应', '10相位'],
        detail: 'ALLRED安全相位：相位切换时强制插入1.5s全红间隔，防止右侧冲突。'
      },
      {
        title: 'Webster 自适应配时',
        icon: '📊',
        level: 4,
        desc: '接收A53传来的各路口排队长度，实时计算最优信号周期C=(1.5L+5)/(1-Y)，动态调整各相位绿灯时长。',
        tags: ['Webster算法', '自适应配时', '排队长度', '动态周期'],
        detail: '周期范围[40s, 120s]，饱和度y_sum>0.9时强制使用最大周期，防止过饱和死锁。'
      },
      {
        title: 'CAN 总线通信',
        icon: '🔌',
        level: 4,
        desc: 'AXI CAN IP，500Kbps，ID 0x101发送信号相位，ID 0x200接收控制命令，ISR处理接收帧，<2ms响应延迟。',
        tags: ['AXI CAN', '500Kbps', 'ISR处理', 'CAN协议'],
        detail: 'CAN帧DLC=4，data[0]=相位，data[1]=剩余秒，data[2:3]=标志位（自适应/安全模式）。'
      },
      {
        title: 'OpenAMP/RPMsg',
        icon: '🔗',
        level: 4,
        desc: 'A53 Linux→R5 FreeRTOS进程间通信，共享内存0xB8000000，传递队列长度、配时命令、心跳，延迟<5ms。',
        tags: ['OpenAMP', 'RPMsg', '共享内存', '跨核通信'],
        detail: 'R5端使用metal_io_read32/write32访问共享内存，A53端通过/dev/rpmsgX字符设备收发消息。'
      },
      {
        title: 'TCM 实时优化',
        icon: '💾',
        level: 4,
        desc: 'ATCM 64KB存放中断向量+CAN ISR+FSM热路径代码，零等待延迟。BTCM 64KB存放栈空间。链接脚本精确控制内存布局。',
        tags: ['ATCM/BTCM', '链接脚本LD', '零等待访问', '实时优化'],
        detail: '.text.isr和.text.can section强制放置在ATCM，确保ISR执行无cache miss。'
      }
    ]
  },
  cloud: {
    title: '云边协同层',
    subtitle: 'MQTT/TLS · gRPC · OTA升级 · SQLite离线缓存 · 安全启动',
    cards: [
      {
        title: 'MQTT/TLS 数据上报',
        icon: '☁️',
        level: 5,
        desc: 'Mosquitto客户端，双向TLS证书认证，QoS=1，主题树traffic/edge/{city}/{district}/{device_id}/{type}，压缩JSON payload。',
        tags: ['MQTT 5.0', 'TLS 1.3', 'QoS=1', 'Mosquitto 2.x'],
        detail: '流量统计每分钟上报，违规事件实时上报含JPEG截图（base64），SQLite离线缓存断网数据。'
      },
      {
        title: 'gRPC 管理服务',
        icon: '🔧',
        level: 4,
        desc: '15个RPC接口：设备状态/实时流/OTA控制/信号灯手动干预/配置下发。StreamDetections实现服务端流式推送。',
        tags: ['gRPC 1.54', 'Protobuf 3', '服务端流', 'TLS双向认证'],
        detail: 'traffic_edge.proto定义TrafficEdge服务，grpc::ServerBuilder监听50051端口，主线程阻塞。'
      },
      {
        title: 'SQLite 离线缓存',
        icon: '💾',
        level: 4,
        desc: '网络中断时，统计数据写入本地SQLite，重连后自动批量上报。环形缓冲最大保留7天数据，防止磁盘满。',
        tags: ['SQLite 3', '离线缓存', '自动重传', '环形缓冲'],
        detail: 'WAL模式提升写入性能，事务批量插入，重连后SELECT排序上报，避免时序乱序。'
      },
      {
        title: 'SWUpdate OTA 升级',
        icon: '🔄',
        level: 4,
        desc: 'A/B双分区eMMC布局，OTA包RSA签名验证，升级失败自动bootcount回滚，支持差分升级减小包体积。',
        tags: ['SWUpdate', 'A/B分区', 'RSA签名', '自动回滚'],
        detail: 'U-Boot读取bootcount变量，>3次失败自动切换到备用分区，保证设备永不变砖。'
      },
      {
        title: '安全启动链',
        icon: '🔐',
        level: 5,
        desc: '完整信任链：BootROM→FSBL(RSA-4096)→U-Boot→Linux IMA完整性度量。eFUSE烧录公钥哈希，AES-256加密比特流。',
        tags: ['安全启动', 'RSA-4096', 'eFUSE', 'AES-256', 'IMA'],
        detail: 'BBRAM存储AES密钥（断电易失），eFUSE存储RSA公钥哈希（永久），两层防篡改。'
      },
      {
        title: 'Prometheus 监控',
        icon: '📊',
        level: 3,
        desc: '设备侧暴露/metrics端点（CPU/内存/DPU利用率/推理延迟/帧率），Prometheus采集，Grafana大屏展示。',
        tags: ['Prometheus', 'Grafana', 'metrics端点', '告警规则'],
        detail: '自定义gauge: edge_infer_latency_ms, edge_dpu_util_pct, edge_cam_online等12个指标。'
      }
    ]
  }
};

// ═══════════════════════════════════════════════════════════
// 就业技能矩阵
// ═══════════════════════════════════════════════════════════
const SKILLS_DATA = [
  { name: 'Vivado Block Design', category: 'fpga', level: 5, demand: '极高', desc: '主流FPGA SoC开发核心工具' },
  { name: 'Vitis HLS / HLS IP', category: 'fpga', level: 5, demand: '极高', desc: 'C→RTL综合，大幅提升开发效率' },
  { name: 'AXI 总线协议', category: 'fpga', level: 5, demand: '极高', desc: 'FPGA SoC片上互联标准' },
  { name: 'MIPI CSI-2 接口', category: 'fpga', level: 4, demand: '高', desc: 'Camera接入核心接口协议' },
  { name: '时序约束与收敛', category: 'fpga', level: 5, demand: '极高', desc: '决定芯片能否正确工作的关键技能' },
  { name: 'GTH SerDes / 10GbE', category: 'fpga', level: 4, demand: '高', desc: '高速串行通信，工业/通信主流' },
  { name: 'PetaLinux / Yocto', category: 'linux', level: 5, demand: '极高', desc: 'Xilinx嵌入式Linux必备工具链' },
  { name: 'V4L2 / DRM 驱动', category: 'linux', level: 5, demand: '极高', desc: 'Linux媒体框架，摄像头/显示开发' },
  { name: 'Linux 设备树', category: 'linux', level: 5, demand: '极高', desc: '嵌入式Linux硬件描述语言' },
  { name: 'OpenAMP / RPMsg', category: 'linux', level: 4, demand: '高', desc: '多核异构通信，AMP系统必备' },
  { name: 'DMABUF / 零拷贝', category: 'linux', level: 4, demand: '高', desc: '高性能视频处理核心技术' },
  { name: 'C++17 多线程', category: 'linux', level: 5, demand: '极高', desc: '现代C++并发编程' },
  { name: 'YOLOv8 / 目标检测', category: 'ai', level: 5, demand: '极高', desc: '当前工业部署最主流检测模型' },
  { name: 'Vitis AI / 模型量化', category: 'ai', level: 5, demand: '极高', desc: 'FPGA AI部署专属工具链' },
  { name: 'DPU 集成与调试', category: 'ai', level: 5, demand: '极高', desc: 'Xilinx边缘AI核心加速器' },
  { name: 'VART 推理运行时', category: 'ai', level: 4, demand: '高', desc: 'DPU推理API，边缘AI应用必备' },
  { name: 'ByteTrack 多目标跟踪', category: 'ai', level: 4, demand: '高', desc: '视频分析核心算法' },
  { name: 'CTC / OCR', category: 'ai', level: 3, demand: '中', desc: '序列识别（车牌/文字）' },
  { name: 'Zynq UltraScale+ 架构', category: 'system', level: 5, demand: '极高', desc: '异构SoC系统级设计能力' },
  { name: 'FreeRTOS 实时系统', category: 'system', level: 4, demand: '高', desc: 'MCU/R5核实时控制' },
  { name: 'MQTT / gRPC 通信', category: 'system', level: 4, demand: '高', desc: 'IoT/边缘云协同主流协议' },
  { name: '安全启动 / eFUSE', category: 'system', level: 4, demand: '高', desc: '商业产品安全合规必备' },
  { name: 'OTA 固件升级', category: 'system', level: 4, demand: '高', desc: 'IoT产品全生命周期维护' },
  { name: '量产自动化测试', category: 'system', level: 3, demand: '中', desc: '从研发到量产的关键能力' }
];

// ═══════════════════════════════════════════════════════════
// 官方文档资源库
// ═══════════════════════════════════════════════════════════
const RESOURCES_DATA = [
  {
    category: 'board',
    title: 'ZCU102 评估板用户指南',
    doc_id: 'UG1182',
    desc: 'ZCU102硬件详细说明：原理图、连接器定义、FMC接口、电源设计、初始化流程。',
    url: 'https://docs.amd.com/v/u/en-US/ug1182-zcu102-eval-bd',
    tags: ['ZCU102', '开发板', '原理图', 'FMC'],
    importance: 5
  },
  {
    category: 'board',
    title: 'Zynq UltraScale+ MPSoC 技术参考手册',
    doc_id: 'UG1085',
    desc: '芯片完整架构：PS子系统、PL接口、内存控制器、安全功能、电源管理。必读核心手册。',
    url: 'https://docs.amd.com/r/en-US/ug1085-zynq-ultrascale-trm',
    tags: ['Zynq', 'MPSoC', 'PS/PL', 'TRM'],
    importance: 5
  },
  {
    category: 'fpga',
    title: 'Vivado 高级综合（HLS）用户指南',
    doc_id: 'UG902',
    desc: 'Vivado HLS C/C++→RTL综合：pragma指令、界面协议、优化技巧、调试。',
    url: 'https://www.amd.com/content/dam/xilinx/support/documents/sw_manuals/xilinx2020_2/ug902-vivado-high-level-synthesis.pdf',
    tags: ['HLS', 'DATAFLOW', 'pragma', '时序优化'],
    importance: 5
  },
  {
    category: 'fpga',
    title: 'Vitis HLS 用户指南',
    doc_id: 'UG1399',
    desc: 'Vitis HLS（新版本）设计方法：数据流优化、存储器分区、RTL接口、IP导出。',
    url: 'https://docs.amd.com/r/en-US/ug1399-vitis-hls',
    tags: ['Vitis HLS', 'C综合', 'IP导出', 'Cosim'],
    importance: 5
  },
  {
    category: 'fpga',
    title: 'AXI Reference Guide',
    doc_id: 'UG1037',
    desc: 'Vivado AXI互联协议详解：AXI4/AXI4-Lite/AXI4-Stream信号时序、SmartConnect。',
    url: 'https://docs.amd.com/v/u/en-US/ug1037-vivado-axi-reference-guide',
    tags: ['AXI4', 'AXI-Stream', 'SmartConnect', '总线协议'],
    importance: 5
  },
  {
    category: 'fpga',
    title: 'MIPI CSI-2 Receiver Subsystem Product Guide',
    doc_id: 'PG232',
    desc: 'MIPI CSI-2 RX IP核：接口配置、Lane数、像素格式（RAW12）、调试方法。',
    url: 'https://docs.amd.com/r/en-US/pg232-mipi-csi2-rx',
    tags: ['MIPI CSI-2', 'Camera', 'RAW12', 'PG232'],
    importance: 4
  },
  {
    category: 'fpga',
    title: '25G Ethernet Subsystem Product Guide',
    doc_id: 'PG210',
    desc: '10G/25G以太网IP：GTH收发器配置、MAC层、RS-FEC、调试接口。',
    url: 'https://docs.amd.com/r/en-US/pg210-25g-ethernet',
    tags: ['10GbE', '25GbE', 'GTH', 'SerDes'],
    importance: 4
  },
  {
    category: 'linux',
    title: 'PetaLinux 工具参考指南',
    doc_id: 'UG1144',
    desc: 'PetaLinux完整工作流：项目创建、内核配置、rootfs定制、SDK生成、启动。',
    url: 'https://docs.amd.com/r/en-US/ug1144-petalinux-tools-reference-guide',
    tags: ['PetaLinux', 'Yocto', 'BSP', '设备树'],
    importance: 5
  },
  {
    category: 'ai',
    title: 'Vitis AI 用户指南',
    doc_id: 'UG1414',
    desc: 'Vitis AI完整流程：模型量化（PyTorch/TensorFlow）、编译、VART部署、性能分析。',
    url: 'https://docs.amd.com/r/en-US/ug1414-vitis-ai',
    tags: ['Vitis AI 3.5', '模型量化', 'VART', 'DPU部署'],
    importance: 5
  },
  {
    category: 'ai',
    title: 'DPU for Convolutional Neural Networks (PG338)',
    doc_id: 'PG338',
    desc: 'DPU IP核完整文档：架构、配置参数（B1024~B8192）、AXI接口、性能指标。',
    url: 'https://docs.amd.com/r/en-US/pg338-dpu',
    tags: ['DPU B4096', 'CNN加速', 'pg338', '2.5T OPS'],
    importance: 5
  },
  {
    category: 'algo',
    title: 'YOLOv8 官方文档',
    doc_id: 'Ultralytics',
    desc: 'YOLOv8完整文档：模型架构、训练配置、导出格式（ONNX/TFLite/OpenVINO）、部署。',
    url: 'https://docs.ultralytics.com/models/yolov8',
    tags: ['YOLOv8', '目标检测', 'ONNX导出', '模型训练'],
    importance: 5
  },
  {
    category: 'algo',
    title: 'ByteTrack 多目标跟踪',
    doc_id: 'GitHub',
    desc: 'ByteTrack开源实现：BYTE算法原理、低置信度候选匹配、多目标跟踪，MOTA State-of-Art。',
    url: 'https://github.com/FoundationVision/ByteTrack',
    tags: ['ByteTrack', 'MOT', 'IoU匹配', '目标跟踪'],
    importance: 4
  },
  {
    category: 'ip',
    title: 'AXI Video Direct Memory Access (pg020)',
    doc_id: 'PG020',
    desc: 'AXI VDMA IP：视频帧缓冲读写、散点列表、中断、多通道配置。视频系统核心IP。',
    url: 'https://docs.amd.com/r/en-US/pg020-axi-vdma',
    tags: ['AXI VDMA', '视频缓冲', 'DMA', 'pg020'],
    importance: 4
  },
  {
    category: 'ip',
    title: 'AXI CAN Product Guide',
    doc_id: 'PG023',
    desc: 'AXI CAN IP：CAN 2.0B协议、波特率设置、中断处理、工作模式（正常/回环/静默）。',
    url: 'https://docs.amd.com/r/en-US/pg023-axi-can',
    tags: ['AXI CAN', 'CAN总线', '500Kbps', '实时控制'],
    importance: 3
  }
];

// ═══════════════════════════════════════════════════════════
// 架构图节点数据
// ═══════════════════════════════════════════════════════════
const ARCH_NODES = [
  // 外设输入
  { id: 'cam', label: '4路摄像头\n4K@30fps', x: 30, y: 180, w: 110, h: 50, type: 'external', color: '#334155' },
  { id: 'cloud', label: '云端管理\n平台', x: 820, y: 80, w: 110, h: 50, type: 'cloud', color: '#1e3a5f' },
  { id: 'signal', label: '信号灯\n控制器', x: 820, y: 280, w: 110, h: 50, type: 'external', color: '#334155' },
  // PL 区
  { id: 'mipi', label: 'MIPI CSI-2\nRX×4', x: 175, y: 80, w: 110, h: 50, type: 'pl', color: '#1a3a2a' },
  { id: 'isp', label: 'ISP HLS\n去马赛克/WB/NV12', x: 310, y: 80, w: 130, h: 50, type: 'pl', color: '#1a3a2a' },
  { id: 'vdma', label: 'AXI VDMA\n零拷贝写DDR', x: 310, y: 165, w: 130, h: 50, type: 'pl', color: '#1a3a2a' },
  { id: 'dpu', label: 'DPU B4096\n2.5T OPS', x: 175, y: 250, w: 110, h: 60, type: 'ai', color: '#1a2a3a' },
  { id: 'osd', label: 'OSD Overlay\n检测框叠加', x: 310, y: 250, w: 130, h: 50, type: 'pl', color: '#1a3a2a' },
  { id: 'eth', label: '10GbE MAC\nGTH SerDes', x: 175, y: 340, w: 110, h: 50, type: 'pl', color: '#1a3a2a' },
  { id: 'can_pl', label: 'AXI CAN\n500Kbps', x: 310, y: 340, w: 130, h: 50, type: 'pl', color: '#1a3a2a' },
  // DDR4
  { id: 'ddr', label: 'DDR4 4GB\n38.4GB/s', x: 475, y: 200, w: 110, h: 80, type: 'ddr', color: '#2a1a3a' },
  // PS A53
  { id: 'a53', label: 'PS A53×4\nLinux 5.15', x: 615, y: 80, w: 120, h: 50, type: 'ps_a53', color: '#1a2a3a' },
  { id: 'app', label: 'EdgeVision App\nVART+gRPC+MQTT', x: 615, y: 155, w: 120, h: 50, type: 'ps_a53', color: '#1a2a3a' },
  { id: 'mqtt', label: 'MQTT/TLS\n云端上报', x: 615, y: 230, w: 120, h: 50, type: 'cloud_conn', color: '#1a1a3a' },
  // PS R5
  { id: 'r5', label: 'PS R5×2\nFreeRTOS', x: 615, y: 305, w: 120, h: 50, type: 'ps_r5', color: '#3a1a1a' },
  { id: 'fsm', label: '信号FSM\nWebster自适应', x: 615, y: 375, w: 120, h: 50, type: 'ps_r5', color: '#3a1a1a' },
];

const ARCH_CONNECTIONS = [
  { from: 'cam', to: 'mipi', label: 'LVDS×4' },
  { from: 'mipi', to: 'isp', label: 'AXI-Stream' },
  { from: 'isp', to: 'vdma', label: 'NV12流' },
  { from: 'vdma', to: 'ddr', label: 'AXI HP0' },
  { from: 'ddr', to: 'dpu', label: 'AXI HP1' },
  { from: 'dpu', to: 'osd', label: '检测结果' },
  { from: 'osd', to: 'eth', label: 'H.264流' },
  { from: 'eth', to: 'cloud', label: '10GbE' },
  { from: 'can_pl', to: 'signal', label: 'CAN线' },
  { from: 'ddr', to: 'a53', label: 'AXI HP2' },
  { from: 'a53', to: 'app', label: '' },
  { from: 'app', to: 'mqtt', label: '' },
  { from: 'mqtt', to: 'cloud', label: 'TLS' },
  { from: 'app', to: 'r5', label: 'OpenAMP' },
  { from: 'r5', to: 'fsm', label: '' },
  { from: 'fsm', to: 'can_pl', label: '配时命令' },
];

const ARCH_NODE_DETAILS = {
  mipi: {
    title: 'MIPI CSI-2 接收子系统 ×4',
    content: '4路独立MIPI CSI-2 4-Lane接收器，连接到FMC HPC J55接口。支持RAW8/RAW10/RAW12像素格式，最高1.5Gbps/Lane，AXI4-Stream输出到ISP。\n\n关键IP：MIPI CSI-2 RX SS（PG232）\n时钟：FCLK2 150MHz',
    color: '#00FF88'
  },
  isp: {
    title: 'ISP 图像信号处理 HLS IP',
    content: '7级DATAFLOW流水线：\n① BLC黑电平校正\n② 白平衡（R/G/B增益）\n③ Bayer去马赛克\n④ Gamma校正（256-LUT）\n⑤ CCM色彩矩阵\n⑥ RGB→YUV420 NV12转换\n⑦ AXI-Stream输出\n\n处理能力：4K@30fps，II=1，250MHz',
    color: '#00FF88'
  },
  dpu: {
    title: 'DPU B4096 深度学习加速器',
    content: 'Xilinx Deep Learning Processing Unit\n算力：4096 MAC × 2 × 300MHz = 2.5T OPS (INT8)\n\n支持网络：YOLOv8s, ResNet, MobileNet等\n内存接口：AXI HP0 @ 128bit\nPblock：CLOCKREGION_X0Y3:X3Y4\n推理延迟：YOLOv8s < 18ms/帧',
    color: '#00BFFF'
  },
  eth: {
    title: '10GbE 以太网子系统',
    content: 'XXV Ethernet MAC IP + GTH高速收发器\n实际链速：10Gbps（虽命名25G，链速取决于协商）\n参考时钟：156.25MHz\n应用：视频回传、OTA升级、gRPC管理\n\n测试：iperf3回环验证 > 8Gbps（FCT通过标准）',
    color: '#00FF88'
  },
  a53: {
    title: 'PS Cortex-A53 × 4核',
    content: '运行 Linux 5.15 (PetaLinux 2023.1)\nCPU：4× ARM Cortex-A53 @ 1.2GHz\n内存：Linux使用2GB DDR4\n\n任务分工：\n• V4L2视频采集（4线程，SCHED_FIFO pri=80）\n• DPU推理管理（1线程，pri=70）\n• gRPC服务器（主线程）\n• MQTT/TLS上报\n• OTA管理',
    color: '#4488FF'
  },
  r5: {
    title: 'PS Cortex-R5 × 2核',
    content: '运行 FreeRTOS v10.5\nCPU：2× ARM Cortex-R5 @ 500MHz\nTCM：ATCM 64KB + BTCM 64KB（零等待）\n\n任务分工（5个任务）：\n• WDT喂狗 pri=5\n• CAN帧接收 pri=4\n• 信号灯FSM pri=3\n• OpenAMP通信 pri=2\n• 遥测上报 pri=1',
    color: '#FF6B35'
  },
  ddr: {
    title: 'DDR4 内存 4GB @ 38.4GB/s',
    content: '物理内存映射：\n0x0000_0000  Linux系统（2GB）\n0x8000_0000  视频帧缓冲（192MB）\n             4路×3帧×NV12\n0x8C00_0000  DPU工作内存（704MB）\n0xB800_0000  RPMsg共享（128MB）\n0xC000_0000  R5私有堆（1GB）\n\n带宽：DDR4-2400 64bit = 38.4GB/s',
    color: '#AA44FF'
  },
  app: {
    title: 'EdgeVision 主应用',
    content: 'C++17多线程应用\n• VART推理引擎（YOLOv8+LPRNet+ByteTrack）\n• 事件检测（6类违规行为）\n• gRPC服务端（15个RPC接口）\n• MQTT/TLS上报客户端\n• OSD寄存器控制（/dev/uio0）\n• SQLite离线缓存',
    color: '#4488FF'
  },
  fsm: {
    title: '信号灯状态机',
    content: '10个信号相位 + Webster自适应配时\n\n相位序列：\nNS绿→NS黄→ALLRED→EW绿→EW黄→ALLRED→\n左转NS绿→ALLRED→左转EW绿→ALLRED\n\nWebster公式：\nC = (1.5L + 5) / (1 - Y)\n周期范围：[40s, 120s]\n\nCAN发送：ID=0x101，DLC=4，<10ms',
    color: '#FF6B35'
  }
};
