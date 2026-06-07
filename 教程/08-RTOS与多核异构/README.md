# 阶段 8：RTOS 与多核异构计算

## 学习目标

- 在 R5 核心上运行 FreeRTOS，处理实时控制任务
- 通过 OpenAMP/RPMsg 实现 A53（Linux）与 R5（FreeRTOS）通信
- 理解 TCM 内存布局与实时性保障（<10ms ISR）
- 实现 A53 异常时 R5 安全接管机制

---

## 8.1 Zynq UltraScale+ 多核架构

```
┌─────────────────────────────────────────────────────┐
│  APU (Application Processing Unit)                  │
│  A53 Core 0-3  @ 1.2 GHz                           │
│  ├── 32KB I/D L1, 1MB L2 共享                       │
│  └── 运行 Linux (PetaLinux)                         │
├─────────────────────────────────────────────────────┤
│  RPU (Real-time Processing Unit)                    │
│  R5 Core 0/1  @ 500 MHz                            │
│  ├── 64KB ATCM (代码，零等待访问)                    │
│  ├── 64KB BTCM (数据，零等待访问)                    │
│  └── 运行 FreeRTOS (实时控制)                       │
├─────────────────────────────────────────────────────┤
│  通信层                                              │
│  ├── OpenAMP RPMsg（共享内存 + SGI 中断通知）        │
│  ├── OCM (On-Chip Memory, 256KB, 两侧均可访问)       │
│  └── DDR4 共享区域（需要 cache 一致性管理）           │
└─────────────────────────────────────────────────────┘
```

---

## 8.2 实验 8-1：R5 FreeRTOS 信号灯控制

对应本项目 `software/r5_freertos/signal_fsm.c`。

### 8.2.1 TCM 内存布局

```c
// lscript.ld - R5 链接脚本（TCM优先）
MEMORY {
    psu_r5_0_atcm_MEM_0 : ORIGIN = 0x00000000, LENGTH = 0x10000  /* 64KB ATCM */
    psu_r5_0_btcm_MEM_0 : ORIGIN = 0x00020000, LENGTH = 0x10000  /* 64KB BTCM */
    psu_ddr_0_MEM_0     : ORIGIN = 0x00100000, LENGTH = 0x7FF00000
}

SECTIONS {
    .text  : { *(.vectors) *(.text) } > psu_r5_0_atcm_MEM_0  /* 代码放 ATCM */
    .data  : { *(.data) }             > psu_r5_0_btcm_MEM_0  /* 数据放 BTCM */
    .bss   : { *(.bss) }              > psu_r5_0_btcm_MEM_0
    .heap  : { }                      > psu_ddr_0_MEM_0
    .stack : { }                      > psu_r5_0_atcm_MEM_0
}
```

### 8.2.2 FreeRTOS 任务优先级设计

```c
// 任务优先级（R5 FreeRTOS，高优先级=高数字）
#define TASK_PRIO_SAFETY     (configMAX_PRIORITIES - 1)  // 7: 安全监控（最高）
#define TASK_PRIO_SIGNAL_FSM (configMAX_PRIORITIES - 2)  // 6: 信号灯状态机
#define TASK_PRIO_CAN_TX     (configMAX_PRIORITIES - 3)  // 5: CAN 发送
#define TASK_PRIO_RPMSG_RX   (configMAX_PRIORITIES - 4)  // 4: RPMsg 接收
#define TASK_PRIO_IDLE_MON   (tskIDLE_PRIORITY + 1)      // 1: 空闲监控

// 主要任务结构
void vSignalFSMTask(void *pvParameters);     // 100ms tick，Webster 计时
void vCANTxTask(void *pvParameters);         // 相位变更时发送 CAN 帧
void vRPMsgRxTask(void *pvParameters);       // 接收 A53 命令（排队长度等）
void vSafetyMonitorTask(void *pvParameters); // 检测 A53 心跳，30s 超时切安全模式
```

### 8.2.3 中断延迟验证（<10ms 目标）

```c
// GPIO 输入中断 → 中断延迟测量
void gpio_isr(void *data) {
    // 读取当前时间戳（TTC 计数器，分辨率 10ns）
    u32 ts = Xil_In32(XPAR_XTTCPS_0_BASEADDR + XTTCPS_COUNT_VALUE_OFFSET);
    u32 latency_ns = (ts - g_gpio_trigger_ts) * 10;  // 10ns/cycle @ 100MHz
    configASSERT(latency_ns < 10000000UL);  // <10ms 断言
    xprintf("IRQ latency: %u us\n", latency_ns / 1000);
}
```

---

## 8.3 实验 8-2：OpenAMP RPMsg 双向通信

### 8.3.1 A53 Linux 侧（remoteproc + rpmsg）

```bash
# 加载 R5 固件（通过 remoteproc 框架）
echo -n "r5_signal_ctrl.elf" > /sys/class/remoteproc/remoteproc0/firmware
echo start > /sys/class/remoteproc/remoteproc0/state

# 查看 RPMsg 通道
ls /dev/rpmsg*   # /dev/rpmsg0

# Python 通信（A53 → R5 发送排队数据）
python3 -c "
import struct, os
fd = os.open('/dev/rpmsg0', os.O_RDWR)

# MSG_TYPE_QUEUE_DATA: type(1B) + ns(2B) + ew(2B) + ... 
msg = struct.pack('<BHH', 0x01, 85, 62)  # 南北85m, 东西62m
os.write(fd, msg)

# 读取响应
resp = os.read(fd, 16)
print('R5 resp:', resp.hex())
os.close(fd)
"
```

### 8.3.2 R5 FreeRTOS 侧（RPMsg 接收）

```c
// rpmsg_handler.c
#include "openamp/open_amp.h"
#include "metal/alloc.h"

static struct rpmsg_endpoint ept;

static int rpmsg_recv_callback(struct rpmsg_endpoint *ept,
                                void *data, size_t len,
                                uint32_t src, void *priv) {
    struct rpmsg_msg *msg = (struct rpmsg_msg *)data;

    switch (msg->type) {
    case MSG_TYPE_QUEUE_DATA:
        // 更新 Webster 计算用的排队长度
        signal_fsm_update_queue(msg->ns_queue_m, msg->ew_queue_m);
        g_a53_last_hb = xTaskGetTickCount();  // 重置心跳计时器
        break;

    case MSG_TYPE_HEARTBEAT:
        g_a53_last_hb = xTaskGetTickCount();
        break;

    case MSG_TYPE_ALLRED_CMD:
        signal_fsm_force_allred(msg->duration_ms);
        break;
    }

    // 回复 ACK
    uint8_t ack[4] = {0xAC, 0x00, 0x00, 0x00};
    rpmsg_send(ept, ack, 4);
    return 0;
}

void rpmsg_init(void) {
    // ... 初始化 OpenAMP 虚拟总线
    rpmsg_create_ept(&ept, rpdev, "signal_ctrl",
                     RPMSG_ADDR_ANY, RPMSG_ADDR_ANY,
                     rpmsg_recv_callback, NULL);
}
```

### 8.3.3 共享内存地址映射

```
OCM 布局（256KB，A53 和 R5 均可访问）:
0xFFFC0000 - 0xFFFC0FFF  VirtIO Ring 0（A53→R5）
0xFFFC1000 - 0xFFFC1FFF  VirtIO Ring 1（R5→A53）
0xFFFC2000 - 0xFFFCFFFF  RPMsg 共享消息缓冲区
0xFFFD0000 - 0xFFFDFFFF  实时状态共享区（无锁读）
0xFFFE0000 - 0xFFFFFFFF  R5 异常向量 + 系统控制
```

---

## 8.4 实验 8-3：A53 故障时 R5 安全接管

```c
// safety_monitor.c - R5 安全监控任务
#define A53_HB_TIMEOUT_MS  30000UL  // 30 秒

void vSafetyMonitorTask(void *pvParameters) {
    TickType_t last_hb = xTaskGetTickCount();

    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(1000));

        TickType_t now = xTaskGetTickCount();
        if ((now - g_a53_last_hb) > pdMS_TO_TICKS(A53_HB_TIMEOUT_MS)) {
            if (!g_safe_mode_active) {
                xprintf("[SAFETY] A53 心跳超时，切换固定配时模式\n");
                g_safe_mode_active = true;

                // 切换到固定配时（Webster 自适应关闭）
                signal_fsm_set_safe_mode(true);

                // 通过 AXI CAN 广播告警帧
                can_send_alarm(CAN_ALARM_A53_LOST);
            }
        }
    }
}
```

---

## 参考资源

| 资源 | 链接/编号 | 说明 |
|------|-----------|------|
| OpenAMP 教程 | [Vitis-Tutorials/Embedded_Software/OpenAMP](https://github.com/Xilinx/Vitis-Tutorials/tree/master/Embedded_Software/Introduction_to_OpenAMP) | 官方 OpenAMP 教程 |
| FreeRTOS on UltraScale+ | [embeddedsw/ThirdParty/bsp/freertos10_xilinx](https://github.com/Xilinx/embeddedsw/tree/master/ThirdParty/bsp/freertos10_xilinx) | FreeRTOS BSP |
| UG1085 | Zynq UltraScale+ MPSoC 技术参考手册 | TCM/OCM/中断系统 |
| UG1137 | Zynq UltraScale+ MPSoC 软件开发指南 v3.0 | 多核启动 + RPMsg |
| OpenAMP GitHub | [github.com/OpenAMP/open-amp](https://github.com/OpenAMP/open-amp) | OpenAMP 库源码 |

详见 [`refs/`](refs/) 目录。
