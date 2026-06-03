/*
 * Cortex-R5 链接脚本
 * ZCU102 R5_0 独立模式：使用 TCM + OpenAMP 共享 DDR
 *
 * 内存布局（R5_0 独立模式）：
 *   ATCM: 0x0000_0000, 64KB  → 中断向量 + 关键代码
 *   BTCM: 0x0002_0000, 64KB  → 实时数据（ISR 栈、环形缓冲区）
 *   DDR:  0xB800_0000, 128MB → OpenAMP 共享内存（PS 保留）
 *         0xC000_0000, 256MB → R5 堆/栈（非实时数据）
 */

_STACK_SIZE    = 0x4000;   /* 16KB 主栈 */
_IRQ_STACK_SIZE = 0x2000;  /* 8KB  IRQ 栈 */
_FIQ_STACK_SIZE = 0x1000;  /* 4KB  FIQ 栈 */
_HEAP_SIZE     = 0x30000;  /* 192KB 堆（FreeRTOS heap_4）*/

MEMORY {
    /* Tightly Coupled Memory A（最低延迟：1 cycle）*/
    ATCM  (rwx) : ORIGIN = 0x00000000, LENGTH = 64K

    /* Tightly Coupled Memory B（实时数据）*/
    BTCM  (rw)  : ORIGIN = 0x00020000, LENGTH = 64K

    /* DDR - OpenAMP 共享内存区（与 A53 Linux 协商的地址）*/
    DDR_RPMSG (rw) : ORIGIN = 0xB8000000, LENGTH = 8M

    /* DDR - R5 私有堆栈区 */
    DDR_R5    (rw) : ORIGIN = 0xC0000000, LENGTH = 64M
}

SECTIONS {
    /* 中断向量表：必须在 ATCM 起始地址 */
    .vectors : {
        KEEP(*(.vectors))
    } > ATCM

    /* 关键代码：放 ATCM 保证最低延迟 */
    .text.isr : {
        *(.text.isr*)      /* ISR 处理函数 */
        *(.text.can*)      /* CAN 收发（实时性要求高）*/
        *(.text.pps*)      /* PPS 同步 */
    } > ATCM

    /* 其余代码：放 DDR（TCM 空间有限）*/
    .text : {
        *(.text*)
        *(.rodata*)
    } > DDR_R5

    /* 初始化数据（从 DDR 加载到 BTCM 运行）*/
    .data_btcm : {
        _data_btcm_start = .;
        *(.data.btcm*)     /* 标记需要放 BTCM 的变量 */
        _data_btcm_end = .;
    } > BTCM AT > DDR_R5

    /* BSS：实时变量放 BTCM */
    .bss.btcm (NOLOAD) : {
        *(.bss.btcm*)
        *(.noinit.btcm*)
    } > BTCM

    /* OpenAMP 共享内存（固定地址，与设备树对齐）*/
    .rpmsg_shm (NOLOAD) : {
        *(.rpmsg_shm*)
        _rpmsg_shm_start = ORIGIN(DDR_RPMSG);
        . = ORIGIN(DDR_RPMSG) + LENGTH(DDR_RPMSG);
        _rpmsg_shm_end = .;
    } > DDR_RPMSG

    /* 普通数据段 */
    .data : {
        *(.data*)
    } > DDR_R5

    .bss (NOLOAD) : {
        __bss_start = .;
        *(.bss*)
        *(COMMON)
        __bss_end = .;
    } > DDR_R5

    /* 堆（FreeRTOS heap_4 使用此区域）*/
    .heap (NOLOAD) : {
        _heap_start = .;
        . += _HEAP_SIZE;
        _heap_end = .;
    } > DDR_R5

    /* 主栈 */
    .stack (NOLOAD) : {
        . = ALIGN(8);
        _stack_end = .;
        . += _STACK_SIZE;
        _stack_start = .;
    } > DDR_R5

    /* IRQ/FIQ 栈（放 BTCM 以降低中断延迟）*/
    .irq_stack (NOLOAD) : {
        . = ALIGN(8);
        _irq_stack_end = .;
        . += _IRQ_STACK_SIZE;
        _irq_stack_start = .;
    } > BTCM

    /* 符号表信息（调试用）*/
    .debug_info   0 : { *(.debug_info)   }
    .debug_abbrev 0 : { *(.debug_abbrev) }
    .debug_line   0 : { *(.debug_line)   }
    .debug_frame  0 : { *(.debug_frame)  }
}
