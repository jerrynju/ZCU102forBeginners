# 阶段 9：系统集成与调试

## 学习目标

- 使用 ILA（Integrated Logic Analyzer）在线抓取 PL 内部信号
- 使用 VIO（Virtual I/O）动态控制 PL 信号
- 进行系统性能分析（AXI 带宽、DPU 利用率）
- 实现 OTA 固件升级（SWUpdate A/B 分区）
- 掌握系统级调试策略（软硬件协同）

---

## 9.1 ILA 在线逻辑分析

### 9.1.1 在 Block Design 中插入 ILA

```tcl
# 方式一：通过 Vivado GUI 标记探针
# 右键信号 → Mark Debug

# 方式二：Tcl 脚本插入（精确控制）
create_bd_cell -type ip -vlnv xilinx.com:ip:ila:6.2 ila_0
set_property -dict [list \
    CONFIG.C_NUM_OF_PROBES  {8}    \
    CONFIG.C_DATA_DEPTH     {4096} \
    CONFIG.C_TRIGOUT_EN     {0}    \
    CONFIG.C_ADV_TRIGGER    {true} \
] [get_bd_cells ila_0]

# 连接探针到 AXI 总线信号
connect_bd_net [get_bd_pins ila_0/clk] [get_bd_pins proc_sys_reset_0/slowest_sync_clk]
connect_bd_net [get_bd_pins ila_0/probe0] [get_bd_pins axi_dma_0/mm2s_prmry_reset_out_n]
connect_bd_net [get_bd_pins ila_0/probe1] [get_bd_pins axi_dma_0/axi_mm2s_tvalid]
# ... 连接其余探针
```

### 9.1.2 ChipScope 触发配置

```tcl
# Vivado Hardware Manager Tcl
connect_hw_server
open_hw_target

# 配置 ILA 触发（AXI TVALID 上升沿）
set_property TRIGGER_COMPARE_VALUE eq1'b1 \
    [get_hw_probes axi_dma_0_mm2s_tvalid -of_objects [get_hw_ilas hw_ila_1]]
set_property CONTROL.TRIGGER_POSITION 512 [get_hw_ilas hw_ila_1]

run_hw_ila [get_hw_ilas hw_ila_1]
wait_on_hw_ila [get_hw_ilas hw_ila_1]

# 上传并保存波形
upload_hw_ila_data [get_hw_ilas hw_ila_1]
write_hw_ila_data ./capture.ila
```

### 9.1.3 AXI 性能监控（APM IP）

```tcl
# 添加 AXI Performance Monitor
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_perf_mon:5.0 axi_perf_mon_0
set_property -dict [list \
    CONFIG.C_NUM_MONITOR_SLOTS {2}    \
    CONFIG.C_ENABLE_EVENT_LOG  {1}    \
] [get_bd_cells axi_perf_mon_0]
```

```c
// 读取 APM 性能计数器（C API）
#include "xaxipmon.h"

XAxiPmon apm;
XAxiPmon_Initialize(&apm, XPAR_AXIPMON_0_DEVICE_ID);
XAxiPmon_StartCounters(&apm, 0);
// ... 运行被测代码 ...
XAxiPmon_StopCounters(&apm, 0);

u64 wr_bytes = XAxiPmon_GetWriteByteCount(&apm, 0);
u64 rd_bytes = XAxiPmon_GetReadByteCount(&apm, 0);
xprintf("AXI HP0 Write: %llu MB/s, Read: %llu MB/s\n",
        wr_bytes / 1048576, rd_bytes / 1048576);
```

---

## 9.2 VIO 动态信号控制

```tcl
# 插入 VIO IP（4 输入探针 + 4 输出探针）
create_bd_cell -type ip -vlnv xilinx.com:ip:vio:3.0 vio_0
set_property -dict [list \
    CONFIG.C_NUM_PROBE_IN  {4} \
    CONFIG.C_NUM_PROBE_OUT {4} \
    CONFIG.C_PROBE_IN0_WIDTH  {1}  \
    CONFIG.C_PROBE_OUT0_WIDTH {8}  \
] [get_bd_cells vio_0]

# 在 Hardware Manager 中动态修改输出值：
# vio probe out[0] = 0xFF (点亮所有LED)
set_property OUTPUT_VALUE 0xFF \
    [get_hw_probes hw_vio_1_vio_trig_out_0 -of_objects [get_hw_vios hw_vio_1]]
commit_hw_vio [get_hw_vios hw_vio_1]
```

---

## 9.3 系统性能分析

### 9.3.1 DPU 利用率分析

```bash
# 在 ZCU102 上运行 DPU 性能分析器
/usr/bin/dpu_runner_benchmark \
    -m yolov8s_traffic.xmodel \
    -t 1 -s 1000 \
    --profiler enable

# 输出示例：
# DPU Load: 87.3%
# Memory BW: 12.8 GB/s (HP0+HP1)
# Throughput: 8.2 FPS
# Latency P50: 118ms, P99: 142ms
```

### 9.3.2 Linux Perf 性能分析（A53）

```bash
# 采集 A53 性能计数器
perf stat -e cache-misses,cache-references,instructions,cycles \
    python3 sim/traffic_sim.py --frames 100 --fast

# 火焰图
perf record -g -F 99 -p $(pgrep traffic_edge) -- sleep 30
perf script | FlameGraph/stackcollapse-perf.pl | FlameGraph/flamegraph.pl > flame.svg
```

---

## 9.4 OTA 固件升级（SWUpdate A/B 分区）

### 9.4.1 分区方案

```
eMMC / SD 卡布局：
├── /dev/mmcblk0p1  boot-a (FAT32, 512MB)  ← 当前运行
├── /dev/mmcblk0p2  boot-b (FAT32, 512MB)  ← OTA 写入目标
├── /dev/mmcblk0p3  rootfs-a (ext4, 4GB)   ← 当前运行
├── /dev/mmcblk0p4  rootfs-b (ext4, 4GB)   ← OTA 写入目标
└── /dev/mmcblk0p5  data (ext4, 剩余)      ← 用户数据（不覆盖）
```

### 9.4.2 SWUpdate 配置

```bash
# 安装 SWUpdate
petalinux-config -c rootfs
# 勾选：CONFIG_SWUPDATE=y

# sw-description（更新包描述文件）
cat > sw-description << 'EOF'
software =
{
    version = "1.2.0";
    hardware-compatibility = ["ZCU102-RevD"];

    images: (
    {
        filename = "BOOT.BIN";
        type = "raw";
        device = "/dev/mmcblk0p2";
        installed-directly = true;
    },
    {
        filename = "rootfs.ext4.gz";
        type = "rawfile";
        device = "/dev/mmcblk0p4";
        compressed = "zlib";
    }
    );
    scripts: (
    {
        filename = "post_install.sh";
        type = "shellscript";
    }
    );
}
EOF

# 打包更新镜像
swupdate-progress -l
```

### 9.4.3 U-Boot A/B 切换

```bash
# U-Boot 环境变量（A/B 切换逻辑）
setenv bootcmd 'run boot_ab_check'
setenv boot_ab_check '
    if test "${boot_slot}" = "b"; then
        setenv bootpart 2; setenv rootpart 4;
    else
        setenv bootpart 1; setenv rootpart 3;
    fi;
    run do_boot'
setenv do_boot 'fatload mmc 0:${bootpart} ${kernel_addr_r} Image;
    fatload mmc 0:${bootpart} ${fdt_addr_r} system.dtb;
    booti ${kernel_addr_r} - ${fdt_addr_r}'
saveenv
```

---

## 9.5 调试策略总结

| 问题类型 | 工具 | 方法 |
|----------|------|------|
| PL 信号问题 | ILA + ChipScope | 触发抓取 AXI/自定义信号 |
| PL 动态控制 | VIO | 在线修改控制寄存器 |
| AXI 总线性能 | APM IP | 统计带宽/延迟 |
| Linux 应用性能 | perf + 火焰图 | 找出 CPU 热点 |
| DPU 推理性能 | dpu_runner_benchmark | 测量吞吐/延迟 |
| 启动问题 | UART + JTAG | 查看 U-Boot/FSBL 日志 |
| 内存问题 | Valgrind / AddressSanitizer | 检测越界/泄漏 |

---

## 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| ILA 产品指南 | PG172 | ILA IP 完整手册 |
| VIO 产品指南 | PG159 | VIO IP 手册 |
| Vivado 调试教程 | [Vivado-Design-Tutorials/Design_Analysis](https://github.com/Xilinx/Vivado-Design-Tutorials/tree/master/Design_Analysis) | 官方调试分析教程 |
| SWUpdate 文档 | [sbabic.github.io/swupdate](https://sbabic.github.io/swupdate) | SWUpdate 官方文档 |
| UG908 | Vivado 实现用户指南 | 时序分析/布线 |

详见 [`refs/`](refs/) 目录。
