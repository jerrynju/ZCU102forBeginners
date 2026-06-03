#pragma once
#include "FreeRTOS.h"
#include "queue.h"
#include <stdint.h>
#include <stdbool.h>

// ── 信号灯相位定义 ────────────────────────────────────────
typedef enum {
    PHASE_NS_GREEN   = 0,  // 南北直行绿灯
    PHASE_NS_YELLOW  = 1,  // 南北黄灯（清场）
    PHASE_NS_LEFT    = 2,  // 南北左转绿灯
    PHASE_NS_LEFT_Y  = 3,  // 南北左转黄灯
    PHASE_EW_GREEN   = 4,  // 东西直行绿灯
    PHASE_EW_YELLOW  = 5,  // 东西黄灯
    PHASE_EW_LEFT    = 6,  // 东西左转绿灯
    PHASE_EW_LEFT_Y  = 7,  // 东西左转黄灯
    PHASE_ALLRED     = 8,  // 全红（相位间隔保护）
    PHASE_FLASH_YEL  = 9,  // 闪烁黄灯（夜间 / 故障）
    PHASE_COUNT
} SignalPhase_t;

// ── 来自 A53 的控制指令 ────────────────────────────────────
typedef enum {
    CMD_SET_TIMING,        // 修改相位时长
    CMD_PHASE_OVERRIDE,    // 强制切换到指定相位
    CMD_ADAPTIVE_ENABLE,   // 开启自适应模式
    CMD_ADAPTIVE_DISABLE,  // 关闭自适应模式
    CMD_ALLRED_HOLD,       // 全红保持（事故处理）
    CMD_RESUME_AUTO,       // 恢复自动控制
    CMD_UPDATE_QUEUE,      // 更新排队长度（用于自适应）
} CtrlCmdType_t;

typedef struct {
    CtrlCmdType_t type;
    SignalPhase_t phase;        // CMD_PHASE_OVERRIDE 使用
    uint32_t      duration_ms;  // 指定时长
    uint32_t      queue_len[4]; // CMD_UPDATE_QUEUE：各方向排队车辆数
} CtrlCmd_t;

// ── 信号灯状态机上下文 ────────────────────────────────────
typedef struct {
    SignalPhase_t current_phase;
    uint32_t      phase_timer_ms;   // 当前相位已运行毫秒数
    uint32_t      phase_duration[PHASE_COUNT]; // 各相位标准时长
    bool          adaptive_enable;
    bool          manual_override;
    uint32_t      queue_len[4];     // 各方向排队车辆数（A53 上报）
    uint32_t      cycle_count;      // 完整周期计数
    bool          safe_mode;        // 安全模式（A53 心跳超时）
} SignalFSM_t;

// ── 对外接口 ──────────────────────────────────────────────
extern QueueHandle_t q_ctrl_cmd;     // 控制指令队列（外部定义）
extern SignalFSM_t   g_signal_fsm;   // 全局状态机实例（只读访问）

void signal_fsm_init(void);
void task_signal_fsm(void *arg);
SignalPhase_t signal_fsm_get_phase(void);
bool signal_fsm_is_red_for_channel(uint8_t channel);

// 返回下一个相位
SignalPhase_t signal_next_phase(SignalPhase_t current);
// 判断指定通道当前是否红灯状态
// channel: 0=南, 1=东, 2=北, 3=西
const char* signal_phase_name(SignalPhase_t phase);
