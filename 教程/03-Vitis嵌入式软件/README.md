# 阶段 3：Vitis 嵌入式软件开发

## 学习目标

- 理解 Vitis 2023.1 平台/域/应用三层工程模型
- 开发 Standalone（裸机）应用：串口、定时器、中断
- 在 A53 核心上运行 FreeRTOS 任务与信号量
- 使用 JTAG/GDB 调试嵌入式程序
- 生成 BOOT.BIN 完成板卡部署

---

## 3.1 Vitis 工程模型

```
Platform Project (platform.xpfm)
│   └── 基于 XSA 硬件描述文件
│
Domain (domain.spfm)
│   ├── standalone_psu_cortexa53_0   # A53 裸机
│   ├── freertos10_xilinx_psu_cortexa53_0  # A53 FreeRTOS
│   └── standalone_psu_cortexr5_0   # R5 裸机
│
Application Project (.xsa → .elf)
    └── main.c + BSP drivers
```

---

## 3.2 实验 3-1：Standalone UART + 定时器

```c
// main.c - 串口 Echo + 定时器中断（每秒打印计数）
#include "xparameters.h"
#include "xuartps.h"
#include "xttcps.h"
#include "xscugic.h"
#include "xil_printf.h"

static volatile u32 tick_count = 0;

void ttc_isr(void *data) {
    XTtcPs *ttc = (XTtcPs *)data;
    XTtcPs_ClearInterruptStatus(ttc, XTtcPs_GetInterruptStatus(ttc));
    tick_count++;
    xil_printf("Tick: %u\r\n", tick_count);
}

int main(void) {
    xil_printf("ZCU102 Standalone Demo\r\n");

    // TTC0 每 1 秒中断
    XTtcPs ttc;
    XTtcPs_Config *cfg = XTtcPs_LookupConfig(XPAR_XTTCPS_0_DEVICE_ID);
    XTtcPs_CfgInitialize(&ttc, cfg, cfg->BaseAddress);
    XTtcPs_SetOptions(&ttc, XTTCPS_OPTION_INTERVAL_MODE | XTTCPS_OPTION_WAVE_DISABLE);
    XTtcPs_SetInterval(&ttc, 100000000UL);  // 100MHz / 100M = 1s
    XTtcPs_EnableInterrupts(&ttc, XTTCPS_IXR_INTERVAL_MASK);

    // GIC 注册 ISR
    XScuGic gic;
    XScuGic_Config *gic_cfg = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
    XScuGic_CfgInitialize(&gic, gic_cfg, gic_cfg->CpuBaseAddress);
    XScuGic_Connect(&gic, XPAR_XTTCPS_0_INTR,
                    (Xil_ExceptionHandler)ttc_isr, &ttc);
    XScuGic_Enable(&gic, XPAR_XTTCPS_0_INTR);
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
        (Xil_ExceptionHandler)XScuGic_InterruptHandler, &gic);
    Xil_ExceptionEnable();
    XTtcPs_Start(&ttc);

    // UART 回环
    XUartPs uart;
    XUartPs_Config *uart_cfg = XUartPs_LookupConfig(XPAR_XUARTPS_0_DEVICE_ID);
    XUartPs_CfgInitialize(&uart, uart_cfg, uart_cfg->BaseAddress);
    XUartPs_SetBaudRate(&uart, 115200);

    u8 buf[64];
    while (1) {
        u32 n = XUartPs_Recv(&uart, buf, sizeof(buf));
        if (n > 0) {
            XUartPs_Send(&uart, buf, n);
        }
    }
}
```

---

## 3.3 实验 3-2：FreeRTOS 多任务

```c
// FreeRTOS 任务：LED 闪烁 + 串口命令处理
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "xgpio.h"
#include "xil_printf.h"

static QueueHandle_t cmd_queue;
static XGpio gpio;

void led_task(void *param) {
    u8 state = 0;
    for (;;) {
        // 等待命令（阻塞 500ms）
        u8 cmd;
        if (xQueueReceive(cmd_queue, &cmd, pdMS_TO_TICKS(500)) == pdTRUE) {
            state = cmd;
        } else {
            state ^= 0x01;  // 心跳闪烁
        }
        XGpio_DiscreteWrite(&gpio, 1, state);
    }
}

void uart_task(void *param) {
    u8 buf[4];
    for (;;) {
        // 阻塞读串口
        if (XUartPs_Recv((XUartPs*)param, buf, 1) > 0) {
            xQueueSend(cmd_queue, &buf[0], 0);
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

int main(void) {
    XGpio_Initialize(&gpio, XPAR_GPIO_0_DEVICE_ID);
    XGpio_SetDataDirection(&gpio, 1, 0x00);

    cmd_queue = xQueueCreate(8, sizeof(u8));
    xTaskCreate(led_task,  "LED",  1024, NULL, 2, NULL);
    xTaskCreate(uart_task, "UART", 1024, NULL, 3, NULL);
    vTaskStartScheduler();
    return 0;
}
```

---

## 3.4 实验 3-3：A53 + R5 双核运行

### 构建步骤

1. 在同一 Vivado 工程生成支持 RPU 的 XSA（使能 RPU 0/1）
2. 创建两个 Domain：
   - `standalone_psu_cortexa53_0`（A53 Core 0）
   - `standalone_psu_cortexr5_0`（R5 Core 0，Split Mode）
3. 分别创建 Application 并编译
4. 使用 `bootgen` 生成 BOOT.BIN

```yaml
# bootgen.bif - 双核镜像
the_ROM_image:
{
    [bootloader, destination_cpu=a53-0] fsbl.elf
    [destination_cpu=a53-0] a53_app.elf
    [destination_cpu=r5-0]  r5_app.elf
}
```

```bash
bootgen -image bootgen.bif -o BOOT.BIN -w on
```

---

## 3.5 JTAG 调试

```bash
# 连接 ZCU102 JTAG（需要 hw_server）
xsct
% connect
% targets
   1  APU
      2  A53 #0 (Running)
      3  A53 #1 (Running)
   5  RPU
      6  R5 #0 (Running)

% target 2         # 选择 A53 #0
% dow a53_app.elf  # 下载 ELF
% bpadd -addr 0x400180  # 断点
% con              # 继续运行
```

---

## 3.6 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| Vitis Embedded Software Dev | [github.com/Xilinx/Vitis-Tutorials/tree/master/Embedded_Software](https://github.com/Xilinx/Vitis-Tutorials/tree/master/Embedded_Software) | 嵌入式软件教程 |
| UG1400 | Vitis 统一软件平台嵌入式软件开发指南 | 完整 Vitis 嵌入式手册 |
| embeddedsw/lib/sw_apps | [github.com/Xilinx/embeddedsw](https://github.com/Xilinx/embeddedsw/tree/master/lib/sw_apps) | 官方裸机示例 |
| FreeRTOS on ZU+ | `embeddedsw/ThirdParty/bsp/freertos10_xilinx` | FreeRTOS BSP |
| UG1283 | Zynq UltraScale+ MPSoC 软件开发指南 | 多核启动流程 |

详见 [`refs/`](refs/) 目录。
