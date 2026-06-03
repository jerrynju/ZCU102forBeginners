"""
信号灯状态机（Python 实现）
与 R5 FreeRTOS 的 signal_fsm.c 逻辑完全对应
用于仿真环境下的信号控制，可选连接 vcan0 进行实际 CAN 通信

Webster 最优配时算法：
    C = (1.5L + 5) / (1 - Y)
    Y = sum(qi / si)  队列流量比
"""

import threading
import time
import struct
import logging
from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class Phase(IntEnum):
    NS_GREEN  = 0
    NS_YELLOW = 1
    ALL_RED_1 = 2
    EW_GREEN  = 3
    EW_YELLOW = 4
    ALL_RED_2 = 5
    COUNT     = 6


PHASE_NAME = {
    Phase.NS_GREEN:  'NS_GREEN',
    Phase.NS_YELLOW: 'NS_YELLOW',
    Phase.ALL_RED_1: 'ALL_RED',
    Phase.EW_GREEN:  'EW_GREEN',
    Phase.EW_YELLOW: 'EW_YELLOW',
    Phase.ALL_RED_2: 'ALL_RED',
}


@dataclass
class SignalState:
    phase:         Phase = Phase.NS_GREEN
    phase_remain_s: float = 5.0
    cycle_s:       float = 60.0
    adaptive_mode: bool  = True
    safe_mode:     bool  = False   # A53失联>30s切换固定时序
    queue_len: List[float] = field(default_factory=lambda: [0.0] * 4)


class SignalFSM:
    """
    信号灯状态机（镜像 R5 FreeRTOS signal_fsm.c）

    默认配时：
      NS_GREEN 5s → NS_YELLOW 1.5s → ALL_RED 0.6s
      EW_GREEN 4s → EW_YELLOW 1.5s → ALL_RED 0.6s
    自适应：Webster 算法动态调整绿灯时长（范围 15s~60s）
    """

    # Webster 参数
    SATURATION_FLOW_PCU_S = 0.5    # 饱和流量（每秒通过的当量乘用车数）
    PHASE_LOST_TIME_S     = 3.0    # 每相位损失时间
    MIN_GREEN_S           = 10.0
    MAX_GREEN_S           = 60.0
    MIN_CYCLE_S           = 40.0
    MAX_CYCLE_S           = 120.0
    YELLOW_S              = 1.5
    ALL_RED_S             = 0.6

    def __init__(self, tick_interval_ms: int = 100,
                 on_phase_change: Optional[Callable] = None,
                 use_vcan: bool = False):
        """
        Args:
            tick_interval_ms: FSM 主循环间隔（与 FreeRTOS xTaskDelayUntil 对应）
            on_phase_change:   相位切换回调 fn(state: SignalState)
            use_vcan:          是否通过 vcan0 发送 CAN 帧
        """
        self.tick_ms         = tick_interval_ms / 1000.0
        self.on_phase_change = on_phase_change
        self.use_vcan        = use_vcan

        self.state = SignalState()
        self._compute_timings()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_a53_heartbeat = time.time()
        self._lock = threading.Lock()

        # CAN socket（可选）
        self._can_sock = None
        if use_vcan:
            self._init_vcan()

        # 命令队列（模拟 OpenAMP RPMsg）
        self.cmd_queue: Queue = Queue(maxsize=32)

    # ─────────────────────────────────────────
    # CAN 接口
    # ─────────────────────────────────────────
    def _init_vcan(self):
        try:
            import socket
            PF_CAN  = 29
            SOCK_RAW_CAN = 3
            CAN_RAW = 1
            self._can_sock = socket.socket(PF_CAN, SOCK_RAW_CAN, CAN_RAW)
            self._can_sock.bind(('vcan0',))
            logger.info("vcan0 CAN socket 已绑定")
        except Exception as e:
            logger.warning(f"vcan0 不可用（{e}），将跳过 CAN 发送")
            self._can_sock = None

    def _send_can_frame(self, phase: Phase, remain_s: float, flags: int = 0):
        """发送 CAN 帧（ID=0x101，DLC=4，与 R5 协议一致）"""
        if not self._can_sock:
            return
        try:
            # struct: can_id(4B) + dlc(1B) + pad(3B) + data(8B)
            can_id  = 0x101
            dlc     = 4
            data    = bytes([int(phase), int(remain_s) & 0xFF,
                             (flags >> 8) & 0xFF, flags & 0xFF])
            frame   = struct.pack('=IB3x8s', can_id, dlc, data.ljust(8, b'\x00'))
            self._can_sock.send(frame)
        except Exception as e:
            logger.debug(f"CAN 发送失败: {e}")

    # ─────────────────────────────────────────
    # Webster 配时计算
    # ─────────────────────────────────────────
    def _compute_timings(self):
        """根据各路口排队长度计算最优周期（Webster公式）"""
        st = self.state
        if not st.adaptive_mode or st.safe_mode:
            # 固定配时（安全模式）
            self._timings = {
                Phase.NS_GREEN:  30.0,
                Phase.NS_YELLOW: self.YELLOW_S,
                Phase.ALL_RED_1: self.ALL_RED_S,
                Phase.EW_GREEN:  25.0,
                Phase.EW_YELLOW: self.YELLOW_S,
                Phase.ALL_RED_2: self.ALL_RED_S,
            }
            return

        # 各进口道流量（用排队长度估算，单位：辆）
        ns_q = (st.queue_len[0] + st.queue_len[2]) / 2.0  # 南北平均
        ew_q = (st.queue_len[1] + st.queue_len[3]) / 2.0  # 东西平均
        S    = self.SATURATION_FLOW_PCU_S

        y_ns = min(0.45, ns_q * 0.1 / S)  # 流量比（限幅防止过饱和）
        y_ew = min(0.45, ew_q * 0.1 / S)
        Y    = y_ns + y_ew

        L    = 2 * self.PHASE_LOST_TIME_S
        if Y >= 0.9:
            C = self.MAX_CYCLE_S
        else:
            C = max(self.MIN_CYCLE_S, min(self.MAX_CYCLE_S,
                    (1.5 * L + 5.0) / (1.0 - Y)))

        # 按流量比分配绿灯时间
        eff_green = C - L
        if y_ns + y_ew > 0:
            g_ns = max(self.MIN_GREEN_S,
                       min(self.MAX_GREEN_S, eff_green * y_ns / (y_ns + y_ew + 1e-6)))
            g_ew = max(self.MIN_GREEN_S,
                       min(self.MAX_GREEN_S, eff_green * y_ew / (y_ns + y_ew + 1e-6)))
        else:
            g_ns = g_ew = eff_green / 2.0

        self._timings = {
            Phase.NS_GREEN:  g_ns,
            Phase.NS_YELLOW: self.YELLOW_S,
            Phase.ALL_RED_1: self.ALL_RED_S,
            Phase.EW_GREEN:  g_ew,
            Phase.EW_YELLOW: self.YELLOW_S,
            Phase.ALL_RED_2: self.ALL_RED_S,
        }
        logger.debug(f"Webster: C={C:.1f}s NS_G={g_ns:.1f}s EW_G={g_ew:.1f}s Y={Y:.3f}")

    # ─────────────────────────────────────────
    # FSM 主循环
    # ─────────────────────────────────────────
    def _fsm_loop(self):
        with self._lock:
            self.state.phase = Phase.NS_GREEN
            self.state.phase_remain_s = self._timings[Phase.NS_GREEN]
        next_tick = time.monotonic() + self.tick_ms

        while self._running:
            now = time.monotonic()
            sleep_t = next_tick - now
            if sleep_t > 0:
                time.sleep(sleep_t)
            next_tick += self.tick_ms

            # 处理命令队列（模拟 RPMsg 接收）
            self._process_commands()

            # A53 心跳检测
            if time.time() - self._last_a53_heartbeat > 30.0:
                if not self.state.safe_mode:
                    logger.warning("A53心跳超时，切换安全模式（固定配时）")
                    with self._lock:
                        self.state.safe_mode = True
                        self._compute_timings()

            with self._lock:
                st = self.state
                st.phase_remain_s -= self.tick_ms
                if st.phase_remain_s <= 0:
                    # 相位切换
                    next_phase = Phase((int(st.phase) + 1) % int(Phase.COUNT))
                    st.phase = next_phase
                    self._compute_timings()
                    st.phase_remain_s = self._timings[next_phase]
                    logger.debug(f"相位切换 → {PHASE_NAME[next_phase]} "
                                 f"(时长={st.phase_remain_s:.1f}s)")
                    flags = (0x01 if st.adaptive_mode else 0) | (0x02 if st.safe_mode else 0)
                    self._send_can_frame(next_phase, st.phase_remain_s, flags)
                    if self.on_phase_change:
                        self.on_phase_change(SignalState(**vars(st)))

    def _process_commands(self):
        """处理来自 A53 的控制命令（对应 RPMsg MSG_TYPE_QUEUE_DATA）"""
        try:
            while True:
                cmd = self.cmd_queue.get_nowait()
                cmd_type = cmd.get('type')
                if cmd_type == 'queue_update':
                    with self._lock:
                        self.state.queue_len = cmd['queue_len']
                        self._compute_timings()
                    self._last_a53_heartbeat = time.time()
                elif cmd_type == 'adaptive_enable':
                    with self._lock:
                        self.state.adaptive_mode = True
                elif cmd_type == 'adaptive_disable':
                    with self._lock:
                        self.state.adaptive_mode = False
                elif cmd_type == 'allred_hold':
                    with self._lock:
                        self.state.phase = Phase.ALL_RED_1
                        self.state.phase_remain_s = cmd.get('duration_s', 5.0)
                elif cmd_type == 'heartbeat':
                    self._last_a53_heartbeat = time.time()
        except Empty:
            pass

    # ─────────────────────────────────────────
    # 公共接口
    # ─────────────────────────────────────────
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._fsm_loop,
                                        name='SignalFSM', daemon=True)
        self._thread.start()
        logger.info("SignalFSM 启动（tick={}ms, adaptive={}, vcan={})".format(
            int(self.tick_ms * 1000), self.state.adaptive_mode, self.use_vcan))

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_state(self) -> SignalState:
        with self._lock:
            import copy
            return copy.deepcopy(self.state)

    def send_queue_update(self, queue_len: List[float]):
        """A53 发送各路口排队长度（单位：米）"""
        self.cmd_queue.put({'type': 'queue_update', 'queue_len': list(queue_len)})

    def send_heartbeat(self):
        """A53 心跳"""
        self.cmd_queue.put({'type': 'heartbeat'})

    def is_red(self, direction: str = 'ns') -> bool:
        with self._lock:
            p = self.state.phase
        if direction == 'ns':
            return p in (Phase.EW_GREEN, Phase.EW_YELLOW,
                         Phase.ALL_RED_1, Phase.ALL_RED_2)
        else:
            return p in (Phase.NS_GREEN, Phase.NS_YELLOW,
                         Phase.ALL_RED_1, Phase.ALL_RED_2)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] %(levelname)s %(message)s')
    changes = []

    def on_change(state: SignalState):
        changes.append(state.phase)
        print(f"  相位切换 → {PHASE_NAME[state.phase]:12s} 剩余={state.phase_remain_s:.1f}s")

    # 使用短相位持续时间（便于快速自测）
    short_phase_dur = {
        Phase.NS_GREEN:  8.0,   # 8s 绿灯（正常17s缩短）
        Phase.NS_YELLOW: 1.5,
        Phase.ALL_RED_1: 0.6,
        Phase.EW_GREEN:  6.0,
        Phase.EW_YELLOW: 1.5,
        Phase.ALL_RED_2: 0.6,
    }
    fsm = SignalFSM(tick_interval_ms=50, on_phase_change=on_change)
    # 覆盖内部配时为短时序（仅测试用）
    fsm._timings = short_phase_dur
    with fsm._lock:
        fsm.state.phase_remain_s = short_phase_dur[Phase.NS_GREEN]
    fsm.start()

    print("信号灯FSM 自测（运行25秒，短相位模式）")
    for i in range(50):
        time.sleep(0.5)
        # 发送低流量心跳（避免Webster把绿灯延长到57s）
        fsm.send_queue_update([2.0, 1.5, 2.5, 1.0])
        fsm.send_heartbeat()
        state = fsm.get_state()
        if i % 4 == 0:
            print(f"  t={i*0.5:.1f}s phase={PHASE_NAME[state.phase]:12s} "
                  f"remain={state.phase_remain_s:.1f}s")

    fsm.stop()
    print(f"\n相位切换次数: {len(changes)}")
    assert len(changes) > 0, "FSM未产生任何相位切换（检查_compute_timings是否覆盖了_timings）"
    print("✓ 信号灯FSM自测通过")
