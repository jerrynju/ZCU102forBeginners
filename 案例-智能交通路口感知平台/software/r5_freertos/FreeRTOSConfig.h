#pragma once
/* FreeRTOS 配置 - Zynq UltraScale+ R5F
 * 参考：Xilinx FreeRTOS BSP for Cortex-R5 */

// ── 基础配置 ──────────────────────────────────────────────
#define configUSE_PREEMPTION            1   /* 抢占式调度 */
#define configUSE_IDLE_HOOK             0
#define configUSE_TICK_HOOK             0
#define configCPU_CLOCK_HZ              500000000UL  /* R5: 500 MHz */
#define configTICK_RATE_HZ              1000UL       /* 1ms tick */
#define configMAX_PRIORITIES            8
#define configMINIMAL_STACK_SIZE        512          /* 字，= 2KB */
#define configTOTAL_HEAP_SIZE           (192 * 1024) /* 192KB（TCM 256KB - 内核/栈）*/
#define configMAX_TASK_NAME_LEN         16
#define configUSE_16_BIT_TICKS          0
#define configIDLE_SHOULD_YIELD         1
#define configUSE_TASK_NOTIFICATIONS    1
#define configTASK_NOTIFICATION_ARRAY_ENTRIES 3

// ── 互斥量和信号量 ────────────────────────────────────────
#define configUSE_MUTEXES               1
#define configUSE_RECURSIVE_MUTEXES     1
#define configUSE_COUNTING_SEMAPHORES   1
#define configQUEUE_REGISTRY_SIZE       8
#define configUSE_QUEUE_SETS            0

// ── 运行时统计 ────────────────────────────────────────────
#define configGENERATE_RUN_TIME_STATS   1
#define configUSE_TRACE_FACILITY        1
#define configUSE_STATS_FORMATTING_FUNCTIONS 1
/* 使用 ARM PMU 计数器作为运行时计时器（比 tick 精度高）*/
#define portCONFIGURE_TIMER_FOR_RUN_TIME_STATS() vConfigureTimerForRunTimeStats()
#define portGET_RUN_TIME_COUNTER_VALUE()          ulGetRunTimeCounterValue()

// ── 软件定时器 ────────────────────────────────────────────
#define configUSE_TIMERS                1
#define configTIMER_TASK_PRIORITY       2
#define configTIMER_QUEUE_LENGTH        10
#define configTIMER_TASK_STACK_DEPTH    256

// ── 协程（不使用）────────────────────────────────────────
#define configUSE_CO_ROUTINES           0

// ── 内存分配 ─────────────────────────────────────────────
/* 使用 heap_4.c（支持碎片合并，适合长期运行）*/
#define configSUPPORT_DYNAMIC_ALLOCATION 1
#define configSUPPORT_STATIC_ALLOCATION  1

// ── Cortex-R5 中断配置 ────────────────────────────────────
#define configUNIQUE_INTERRUPT_PRIORITIES 32
#define configINSTALL_EXCEPTION_HANDLERS  1
/* 允许 FreeRTOS API 调用的最低中断优先级
 * 0 = 最高，31 = 最低（ARM GIC）
 * ISR 中只能调用 xxxFromISR() 变体 */
#define configMAX_API_CALL_INTERRUPT_PRIORITY 18

// ── 断言（调试版本开启）──────────────────────────────────
#ifdef DEBUG
    extern void vAssertCalled(const char* file, int line);
    #define configASSERT(x) if((x) == 0) vAssertCalled(__FILE__, __LINE__)
#else
    #define configASSERT(x)
#endif

// ── 可选功能 ─────────────────────────────────────────────
#define INCLUDE_vTaskPrioritySet        1
#define INCLUDE_uxTaskPriorityGet       1
#define INCLUDE_vTaskDelete             1
#define INCLUDE_vTaskSuspend            1
#define INCLUDE_xResumeFromISR          1
#define INCLUDE_vTaskDelayUntil         1
#define INCLUDE_vTaskDelay              1
#define INCLUDE_xTaskGetSchedulerState  1
#define INCLUDE_xTaskGetCurrentTaskHandle 1
#define INCLUDE_uxTaskGetStackHighWaterMark 1
#define INCLUDE_xTaskGetIdleTaskHandle  1
#define INCLUDE_eTaskGetState           1
#define INCLUDE_xTimerPendFunctionCall  1
#define INCLUDE_xTaskAbortDelay         1
#define INCLUDE_xTaskGetHandle          1
#define INCLUDE_xTaskResumeFromISR      1

// ── 端口专用（ARM Cortex-R5）────────────────────────────
#define configINTERRUPT_CONTROLLER_BASE_ADDRESS  0xF9000000UL  /* GIC-400 */
#define configINTERRUPT_CONTROLLER_CPU_INTERFACE_OFFSET 0x1000UL
