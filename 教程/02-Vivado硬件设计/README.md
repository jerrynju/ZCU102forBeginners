# 阶段 2：Vivado 硬件设计

## 学习目标

- 掌握 IP Integrator (IPI) Block Design 工作流程
- 配置 Zynq UltraScale+ PS（EMIO、AXI 主从端口、中断）
- 集成 AXI GPIO / UART / DMA / BRAM 等常用 IP
- 编写时序约束（XDC），完成布局布线
- 生成 XSA 硬件平台交付 Vitis

---

## 2.1 Zynq UltraScale+ 架构速览

```
┌──────────────────────────────────────────────────────┐
│  Processing System (PS)                              │
│  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  APU A53×4  │  │  RPU R5×2 (TCM 256KB)        │  │
│  │  1.2-1.5GHz │  │  Lockstep / Split Mode       │  │
│  └──────┬───────┘  └──────────────────────────────┘  │
│         │ AXI HP×4 + AXI HPC×2 + AXI ACE                │
│  ┌──────▼───────────────────────────────────────────┐  │
│  │  PS-PL 接口：AXI GP M/S×2, AXI HP S×4, ACP     │  │
│  └──────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│  Programmable Logic (PL) — xczu9eg                   │
│  LUT: 274K  FF: 548K  BRAM: 912×36Kb  DSP: 2520     │
│  GTH×16 (16.375 Gbps)  PCIE×1  CMAC×1               │
└──────────────────────────────────────────────────────┘
```

---

## 2.2 实验 2-1：AXI GPIO LED 控制

### 目标
通过 AXI GPIO IP 控制 ZCU102 板卡上的用户 LED（GPIO_LED[0:7]）。

### 2.2.1 Block Design 步骤

```tcl
# refs/lab2_1_gpio.tcl
create_project lab2_gpio ./lab2_gpio -part xczu9eg-ffvb1156-2-e
set_property board_part xilinx.com:zcu102:part0:3.4 [current_project]
create_bd_design "system"

# 添加 PS
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 zynq_ultra_ps_e_0
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset 1} [get_bd_cells zynq_ultra_ps_e_0]

# 添加 AXI GPIO
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_0
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH {8} \
    CONFIG.C_ALL_OUTPUTS {1} \
] [get_bd_cells axi_gpio_0]

# 自动连线
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config {Master "/zynq_ultra_ps_e_0/M_AXI_HPM0_FPD" Clk "Auto"} \
    [get_bd_intf_pins axi_gpio_0/S_AXI]

# 连接外部端口（LED）
make_bd_intf_pins_external [get_bd_intf_pins axi_gpio_0/GPIO]
set_property name {gpio_led} [get_bd_intf_ports GPIO_0]
```

### 2.2.2 引脚约束（XDC）

```xdc
# refs/zcu102_gpio_led.xdc
set_property PACKAGE_PIN AG14 [get_ports {gpio_led_tri_o[0]}]
set_property PACKAGE_PIN AF13 [get_ports {gpio_led_tri_o[1]}]
set_property PACKAGE_PIN AE13 [get_ports {gpio_led_tri_o[2]}]
set_property PACKAGE_PIN AJ14 [get_ports {gpio_led_tri_o[3]}]
set_property PACKAGE_PIN AJ15 [get_ports {gpio_led_tri_o[4]}]
set_property PACKAGE_PIN AH13 [get_ports {gpio_led_tri_o[5]}]
set_property PACKAGE_PIN AH14 [get_ports {gpio_led_tri_o[6]}]
set_property PACKAGE_PIN AL12 [get_ports {gpio_led_tri_o[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {gpio_led_tri_o[*]}]
```

### 2.2.3 Vitis 软件（C代码）

```c
// 通过 AXI GPIO 控制 LED 流水灯
#include "xgpio.h"
#include "sleep.h"

int main() {
    XGpio gpio;
    XGpio_Initialize(&gpio, XPAR_GPIO_0_DEVICE_ID);
    XGpio_SetDataDirection(&gpio, 1, 0x00);  // 全部输出

    for (int i = 0; ; i++) {
        XGpio_DiscreteWrite(&gpio, 1, 1 << (i % 8));
        usleep(200000);
    }
    return 0;
}
```

---

## 2.3 实验 2-2：AXI DMA + BRAM 数据搬移

### 目标
使用 AXI DMA 在 PS DDR 与 PL BRAM 之间做零拷贝数据传输，理解 AXI4-Stream 总线。

### 2.3.1 Block Design 关键连接

```
PS M_AXI_HPM0_FPD ─────→ AXI DMA (S_AXI_LITE)
PS S_AXI_HP0_FPD  ←───── AXI DMA (M_AXI_MM2S / M_AXI_S2MM)
AXI DMA M_AXIS_MM2S ───→ AXI4-Stream Data FIFO → BRAM Controller
BRAM Controller    ←───── AXI4-Stream Data FIFO ← AXI DMA S_AXIS_S2MM
```

关键 IP 配置：
- `axi_dma_0`: Enable Scatter-Gather = OFF, Data Width = 64, Max Burst = 256
- `axi_bram_ctrl_0`: Data Width = 32, ECC = OFF

### 2.3.2 关键 C 代码片段

```c
// DMA 简单传输（轮询模式）
#include "xaxidma.h"

#define DDR_SRC_ADDR  0x10000000UL
#define BRAM_DST_ADDR 0xA0000000UL
#define LEN_BYTES     1024

XAxiDma dma;
XAxiDma_Config *cfg = XAxiDma_LookupConfig(XPAR_AXIDMA_0_DEVICE_ID);
XAxiDma_CfgInitialize(&dma, cfg);

// 发起 MM2S（DDR → Stream）
XAxiDma_SimpleTransfer(&dma, DDR_SRC_ADDR, LEN_BYTES, XAXIDMA_DMA_TO_DEVICE);
// 等待完成
while (XAxiDma_Busy(&dma, XAXIDMA_DMA_TO_DEVICE));
```

---

## 2.4 实验 2-3：中断系统（GIC + AXI INTC）

### 中断路由关系

```
PL IP 中断信号
    └→ xlconcat_0 (irq[0:7])
         └→ zynq_ultra_ps_e_0 (pl_ps_irq0[7:0])
              └→ GIC SPI [121..128]
                   └→ Linux /proc/interrupts
```

### 关键配置

```c
// FreeRTOS / Standalone 中断注册
#include "xscugic.h"

XScuGic gic;
XScuGic_Config *gic_cfg = XScuGic_LookupConfig(XPAR_SCUGIC_0_DEVICE_ID);
XScuGic_CfgInitialize(&gic, gic_cfg, gic_cfg->CpuBaseAddress);

// 注册 ISR（IRQ ID = 121 对应 PL IRQ[0]）
XScuGic_Connect(&gic, 121, (Xil_ExceptionHandler)my_isr, (void*)&my_data);
XScuGic_Enable(&gic, 121);
Xil_ExceptionEnable();
```

---

## 2.5 时序约束要点

```xdc
# 主时钟（来自 PS PL_CLK0，默认 100 MHz）
create_clock -period 10.000 -name pl_clk0 [get_pins zynq_ultra_ps_e_0/inst/PS8_i/PLCLK[0]]

# I/O 约束（对外部接口）
set_input_delay  -clock pl_clk0 -max 2.0 [get_ports data_in[*]]
set_output_delay -clock pl_clk0 -max 2.0 [get_ports data_out[*]]

# 时序例外（跨时钟域同步信号）
set_false_path -from [get_cells {sync_reg_0}] -to [get_cells {sync_reg_1}]
```

---

## 2.6 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| Vivado Design Tutorials | [github.com/Xilinx/Vivado-Design-Tutorials](https://github.com/Xilinx/Vivado-Design-Tutorials) | 官方 Vivado 教程集 |
| UG994 | Vivado Design Suite IPI 用户指南 | Block Design 完整手册 |
| UG899 | Vivado Design Suite I/O 与时钟规划 | 引脚/时钟约束 |
| PG021 | AXI DMA 产品指南 | DMA 配置与驱动 |
| PG144 | AXI GPIO 产品指南 | GPIO IP 手册 |
| Vivado-Design-Tutorials/Design_Flow/Lab_7_AXI_Peripherals | [GitHub 链接](https://github.com/Xilinx/Vivado-Design-Tutorials/tree/master/Design_Flow) | AXI 外设实验 |

详见 [`refs/`](refs/) 目录。
