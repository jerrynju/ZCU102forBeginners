# @req VP-001, STK-REQ-001, STK-REQ-002
# @design DES-ARCH-004
# @test TC-SIM-001, TC-SIM-002, TC-SIM-003
# @author sim-team | @since 2026-06-04 | @version 1.0
# @status verified
"""
EdgeVision-T1 完整仿真主控器
在无 FPGA/DPU 硬件的情况下，模拟整个数据处理链路：
  [场景生成] → [模拟检测] → [多目标跟踪] → [事件检测] → [信号灯FSM]
                                                          ↓
                                            [MQTT 上报] [统计输出]

用法：
  # 纯仿真（无硬件依赖）
  python3 sim/traffic_sim.py --frames 600

  # 使用真实 ONNX 模型（若有）
  python3 sim/traffic_sim.py --model ai/deploy/traffic_yolov8.onnx

  # 连接本地 MQTT broker
  python3 sim/traffic_sim.py --mqtt localhost --frames 300

  # 显示实时视频窗口（需要图形界面）
  python3 sim/traffic_sim.py --display --frames 300
"""

import sys
import os
import time
import json
import math
import argparse
import logging
import threading
from typing import List, Dict, Optional
from collections import defaultdict, deque

import numpy as np
import cv2

# 将 sim/ 目录加入路径
sys.path.insert(0, os.path.dirname(__file__))

from scene_generator import SceneGenerator, SignalPhase
from mock_detector import create_detector, Detection
from bytetrack_simple import ByteTracker, TrackBox
from signal_fsm import SignalFSM, SignalState, PHASE_NAME

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# 事件检测器（对应 C++ EventDetector）
# ─────────────────────────────────────────────────────────
class EventDetector:
    """检测 6 类交通违规事件"""
    STOP_LINE_Y_NORTH = 240 - 90  # 从南驶向北的停止线 y 坐标（像素）
    STOP_LINE_Y_SOUTH = 240 + 90
    STOP_LINE_X_EAST  = 320 - 90
    STOP_LINE_X_WEST  = 320 + 90
    PARKING_MIN_FRAMES = 90       # 静止超过3秒（30fps×3）判停车

    def __init__(self):
        self._static_count: Dict[int, int] = {}   # track_id → 静止帧计数
        self._last_pos: Dict[int, tuple]    = {}   # track_id → 上次位置
        self.events: list = []                      # 累计事件列表

    def _line_crossed(self, hist: list, line_y: float, direction: str) -> bool:
        """判断轨迹是否穿越水平线"""
        if len(hist) < 2:
            return False
        prev_y = hist[-2][1]
        curr_y = hist[-1][1]
        if direction == 'up':    # 从南向北（y减小）
            return prev_y > line_y >= curr_y
        elif direction == 'down':
            return prev_y < line_y <= curr_y
        return False

    def _line_crossed_x(self, hist: list, line_x: float, direction: str) -> bool:
        if len(hist) < 2:
            return False
        prev_x = hist[-2][0]
        curr_x = hist[-1][0]
        if direction == 'left':
            return prev_x > line_x >= curr_x
        elif direction == 'right':
            return prev_x < line_x <= curr_x
        return False

    def update(self, tracks: List[TrackBox], signal_ns_red: bool,
               signal_ew_red: bool, frame_idx: int) -> list:
        events = []
        cx0, cy0 = 320, 240  # 路口中心

        for trk in tracks:
            tid = trk.track_id
            hist = trk.history

            # ── 闯红灯检测 ──────────────────────────────────
            if signal_ns_red and len(hist) >= 2:
                # NS方向红灯时，检测从南向北穿越停止线
                if self._line_crossed(hist, self.STOP_LINE_Y_NORTH, 'up'):
                    evt = {'type': 'RED_LIGHT_VIOLATION',
                           'track_id': tid, 'cls': trk.cls,
                           'frame': frame_idx,
                           'cx': trk.cx, 'cy': trk.cy}
                    events.append(evt)
                    self.events.append(evt)
                    logger.info(f"[事件] 闯红灯 track_id={tid} cls={trk.cls} 帧#{frame_idx}")

            if signal_ew_red and len(hist) >= 2:
                if self._line_crossed_x(hist, self.STOP_LINE_X_EAST, 'left'):
                    evt = {'type': 'RED_LIGHT_VIOLATION',
                           'track_id': tid, 'cls': trk.cls,
                           'frame': frame_idx,
                           'cx': trk.cx, 'cy': trk.cy}
                    events.append(evt)
                    self.events.append(evt)
                    logger.info(f"[事件] 闯红灯(EW) track_id={tid} cls={trk.cls} 帧#{frame_idx}")

            # ── 违停检测 ──────────────────────────────────
            if tid in self._last_pos:
                lx, ly = self._last_pos[tid]
                move = math.hypot(trk.cx - lx, trk.cy - ly)
                if move < 1.5:
                    self._static_count[tid] = self._static_count.get(tid, 0) + 1
                else:
                    self._static_count[tid] = 0
                # 在路口区域静止超过阈值
                in_intersection = (abs(trk.cx - cx0) < 120 and abs(trk.cy - cy0) < 120)
                if (self._static_count.get(tid, 0) == self.PARKING_MIN_FRAMES
                        and in_intersection and trk.cls != 'person'):
                    evt = {'type': 'ILLEGAL_PARKING',
                           'track_id': tid, 'cls': trk.cls,
                           'frame': frame_idx}
                    events.append(evt)
                    self.events.append(evt)
                    logger.info(f"[事件] 违停 track_id={tid} 帧#{frame_idx}")

            self._last_pos[tid] = (trk.cx, trk.cy)

        return events


# ─────────────────────────────────────────────────────────
# MQTT 上报（可选）
# ─────────────────────────────────────────────────────────
class MQTTReporter:
    def __init__(self, host: str, port: int = 1883,
                 device_id: str = 'sim001', city: str = 'sim'):
        self._connected = False
        self._client    = None
        self.device_id  = device_id
        self.base_topic = f"traffic/edge/{city}/sim/{device_id}"
        self.msg_count  = 0

        try:
            import paho.mqtt.client as mqtt
            self._client = mqtt.Client(client_id=device_id)
            self._client.on_connect = self._on_connect
            self._client.connect_async(host, port, keepalive=30)
            self._client.loop_start()
        except ImportError:
            logger.warning("paho-mqtt 未安装，跳过 MQTT 上报（pip install paho-mqtt）")
        except Exception as e:
            logger.warning(f"MQTT 连接失败（{e}），跳过上报")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info(f"MQTT 已连接 ({self.base_topic})")

    def publish_flow(self, stats: dict):
        self.msg_count += 1
        payload = json.dumps({**stats, 'device_id': self.device_id,
                              'ts': int(time.time())}, ensure_ascii=False)
        if self._connected and self._client:
            self._client.publish(f"{self.base_topic}/flow", payload, qos=1)
        else:
            logger.debug(f"[MQTT] {self.base_topic}/flow → {payload[:80]}")

    def publish_event(self, event: dict):
        payload = json.dumps({**event, 'device_id': self.device_id,
                              'ts': int(time.time())}, ensure_ascii=False)
        if self._connected and self._client:
            self._client.publish(f"{self.base_topic}/event", payload, qos=1)
        logger.debug(f"[MQTT] event → {payload}")

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()


# ─────────────────────────────────────────────────────────
# 主仿真控制器
# ─────────────────────────────────────────────────────────
class TrafficSimulator:
    def __init__(self, args: argparse.Namespace):
        self.args = args

        # 核心模块
        self.scene_gen  = SceneGenerator(seed=args.seed)
        self.detector   = create_detector(
            model_path=getattr(args, 'model', None))
        self.tracker    = ByteTracker()
        self.event_det  = EventDetector()
        self.fsm        = SignalFSM(
            tick_interval_ms=100,
            on_phase_change=self._on_phase_change,
            use_vcan=getattr(args, 'vcan', False))

        # MQTT（可选）
        self.mqtt = None
        if getattr(args, 'mqtt', None):
            self.mqtt = MQTTReporter(host=args.mqtt, device_id='sim001')

        # 统计
        self.stats = {
            'frames_processed': 0,
            'total_detections': 0,
            'total_tracks':     0,
            'events_detected':  0,
            'phase_changes':    0,    # 来自场景生成器的信号相位切换数
            'fsm_phase_changes': 0,   # 来自实时FSM的相位切换数
            'latency_sum_ms':   0.0,
            'latency_count':    0,
        }
        self._minute_counts: Dict[str, int] = defaultdict(int)
        self._last_minute_ts = time.time()
        self._phase_log: list = []
        self._last_scene_phase: Optional[str] = None

    def _on_phase_change(self, state: SignalState):
        self.stats['fsm_phase_changes'] += 1
        self._phase_log.append({
            'phase': state.phase.name,
            'time': time.time(),
        })

    def _draw_overlay(self, frame: np.ndarray, tracks: List[TrackBox],
                      events: list, sig_state: SignalState) -> np.ndarray:
        """在仿真帧上叠加检测框和跟踪ID（可视化用）"""
        cls_colors = {
            'car': (180, 90, 30), 'truck': (50, 80, 180),
            'bus': (30, 150, 180), 'person': (50, 200, 200), 'motorbike': (200, 60, 200)
        }
        for trk in tracks:
            color = cls_colors.get(trk.cls, (150, 150, 150))
            cv2.rectangle(frame, (trk.x1, trk.y1), (trk.x2, trk.y2), color, 2)
            label = f"#{trk.track_id} {trk.cls[:3]} {trk.confidence:.2f}"
            cv2.putText(frame, label, (trk.x1, trk.y1 - 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

        # 右下角信号状态
        phase_str = PHASE_NAME.get(sig_state.phase, str(sig_state.phase))
        remain    = sig_state.phase_remain_s
        cv2.putText(frame, f"SIG:{phase_str} {remain:.1f}s",
                    (4, frame.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (0, 220, 220), 1)

        # 事件提示
        for evt in events:
            cv2.putText(frame, f"! {evt['type'][:20]}",
                        (200, 16), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (0, 0, 255), 2)
        return frame

    def _publish_minute_stats(self):
        """每分钟上报一次流量统计（对应 MQTT flow 主题）"""
        now = time.time()
        if now - self._last_minute_ts < 10.0:  # 仿真中每10秒上报
            return
        self._last_minute_ts = now
        stats = {
            'interval_s':  10,
            'counts':       dict(self._minute_counts),
            'queue_m':      np.random.uniform(10, 40),
            'channel':      0,
        }
        if self.mqtt:
            self.mqtt.publish_flow(stats)
        logger.info(f"[流量统计] {stats['counts']}")
        # 发送排队长度到信号FSM
        self.fsm.send_queue_update([
            stats['queue_m'], stats['queue_m'] * 0.8,
            stats['queue_m'] * 1.1, stats['queue_m'] * 0.6
        ])
        self.fsm.send_heartbeat()
        self._minute_counts.clear()

    def run(self) -> dict:
        """运行仿真主循环，返回最终统计数据"""
        target_fps   = 30
        frame_period = 1.0 / target_fps
        total_frames = self.args.frames
        display      = getattr(self.args, 'display', False)

        self.fsm.start()
        logger.info(f"仿真启动：{total_frames} 帧, FPS={target_fps}, "
                    f"display={display}")

        start_time = time.time()
        latencies  = deque(maxlen=300)

        for fi in range(total_frames):
            t_frame_start = time.monotonic()

            # 1. 生成场景帧
            frame, gt = self.scene_gen.next_frame()
            scene_sig = self.scene_gen.get_signal_state()

            # 2. 检测
            dets, lat_ms = self.detector.detect(frame, gt)
            latencies.append(lat_ms)
            self.stats['total_detections'] += len(dets)
            self.stats['latency_sum_ms']   += lat_ms
            self.stats['latency_count']    += 1

            # 3. 跟踪
            tracks = self.tracker.update(dets)
            self.stats['total_tracks'] = max(
                self.stats['total_tracks'], self.tracker._next_id - 1)

            # 4. 事件检测（使用场景生成器的真实信号状态，与FSM状态解耦）
            events = self.event_det.update(
                tracks,
                signal_ns_red=scene_sig['ns_red'],
                signal_ew_red=scene_sig['ew_red'],
                frame_idx=fi)

            # 统计场景生成器信号相位切换次数（帧级，不依赖实时FSM）
            cur_phase = scene_sig['phase']
            if cur_phase != self._last_scene_phase and self._last_scene_phase is not None:
                self.stats['phase_changes'] += 1
            self._last_scene_phase = cur_phase
            if events:
                self.stats['events_detected'] += len(events)
                for evt in events:
                    if self.mqtt:
                        self.mqtt.publish_event(evt)

            # 5. 统计计数（按类型）
            for trk in tracks:
                self._minute_counts[trk.cls] = self._minute_counts.get(trk.cls, 0)
            for det in dets:
                self._minute_counts[det.class_name] = \
                    self._minute_counts.get(det.class_name, 0) + 1

            # 6. 定期上报
            self._publish_minute_stats()

            self.stats['frames_processed'] += 1

            # 7. 可视化（可选）
            if display or (fi % 90 == 0 and getattr(self.args, 'save_frames', False)):
                viz = self._draw_overlay(frame.copy(), tracks, events,
                                         self.fsm.get_state())
                if display:
                    cv2.imshow('EdgeVision-T1 Simulation', viz)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.info("用户退出")
                        break
                if fi % 90 == 0 and getattr(self.args, 'save_frames', False):
                    cv2.imwrite(f'/tmp/sim_{fi:05d}.jpg', viz)

            # 8. 帧率控制（仿真可以跑得比实时快）
            elapsed = time.monotonic() - t_frame_start
            if not getattr(self.args, 'fast', False):
                sleep_t = frame_period - elapsed
                if sleep_t > 0:
                    time.sleep(sleep_t)

            # 9. 进度打印
            if fi % 150 == 0 and fi > 0:
                elapsed_total = time.time() - start_time
                fps = fi / elapsed_total
                p50 = sorted(latencies)[len(latencies) // 2] if latencies else 0
                logger.info(
                    f"进度: {fi}/{total_frames} ({fi/total_frames*100:.0f}%) "
                    f"FPS={fps:.1f} P50_lat={p50:.1f}ms "
                    f"tracks={len(tracks)} events={self.stats['events_detected']}")

        self.fsm.stop()
        if display:
            cv2.destroyAllWindows()
        if self.mqtt:
            self.mqtt.disconnect()

        total_time = time.time() - start_time
        avg_lat = (self.stats['latency_sum_ms'] / max(1, self.stats['latency_count']))
        self.stats['elapsed_s']       = round(total_time, 2)
        self.stats['effective_fps']   = round(total_frames / total_time, 1)
        self.stats['avg_latency_ms']  = round(avg_lat, 2)
        self.stats['gt_violations']   = len(self.scene_gen.violation_frames)
        return self.stats


# ─────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description='EdgeVision-T1 交通路口仿真器')
    p.add_argument('--frames',  type=int,   default=300,  help='仿真总帧数')
    p.add_argument('--seed',    type=int,   default=42,   help='随机种子（保证可复现）')
    p.add_argument('--model',   type=str,   default=None, help='ONNX 模型路径（不提供则使用 MockDetector）')
    p.add_argument('--mqtt',    type=str,   default=None, help='MQTT broker 地址')
    p.add_argument('--vcan',    action='store_true',      help='使用 vcan0 发送 CAN 帧')
    p.add_argument('--display', action='store_true',      help='显示实时视频窗口（需要图形界面）')
    p.add_argument('--fast',    action='store_true',      help='全速运行（不等待帧率）')
    p.add_argument('--save-frames', action='store_true',  help='每3秒保存一帧到 /tmp/')
    p.add_argument('--log-level', default='INFO',
                   choices=['DEBUG', 'INFO', 'WARNING'])
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s [%(name)s] %(levelname)s %(message)s',
        datefmt='%H:%M:%S')

    print("\n" + "=" * 60)
    print("EdgeVision-T1 闭环仿真验证")
    print(f"  帧数: {args.frames} | 种子: {args.seed} | 快速模式: {args.fast}")
    print(f"  模型: {args.model or 'MockDetector（无硬件依赖）'}")
    print(f"  MQTT: {args.mqtt or '未启用'} | vcan: {args.vcan}")
    print("=" * 60 + "\n")

    sim = TrafficSimulator(args)
    stats = sim.run()

    print("\n" + "=" * 60)
    print("仿真完成 - 统计汇总")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:<25}: {v}")
    print("=" * 60)

    # 验证核心指标
    ok = True
    checks = [
        (stats['frames_processed'] >= args.frames * 0.99, "帧数达标"),
        (stats['effective_fps'] >= 10,                    "有效FPS≥10"),
        (stats['avg_latency_ms'] < 100,                   "推理延迟<100ms"),
        (stats['phase_changes'] >= 2,                     "信号灯相位≥2次切换"),
        (stats['total_tracks'] > 0,                       "产生跟踪ID"),
    ]
    print("\n验证结果:")
    for passed, desc in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}")
        if not passed:
            ok = False

    print("\n" + ("✓ 全部通过" if ok else "✗ 存在失败项") + "\n")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
