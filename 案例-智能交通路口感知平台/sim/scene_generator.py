"""
合成交通路口场景生成器
生成带有移动车辆、行人、信号灯状态的仿真路口视频帧
无需真实摄像头，完全基于 OpenCV 几何绘图

坐标系：640×480 BRG 图像
  ┌─────────────────────────┐
  │   北进口（从上方入）     │
  │  ┌───┐        ┌───┐   │
  │  │   │ 路口区 │   │   │
  │  └───┘        └───┘   │
  │   南进口（从下方入）     │
  └─────────────────────────┘
"""

import cv2
import numpy as np
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import IntEnum


# ─────────────────────────────────────────────
# 常量定义
# ─────────────────────────────────────────────
W, H = 640, 480
CENTER = (W // 2, H // 2)
LANE_W = 36          # 车道宽（像素）
ROAD_W = LANE_W * 4  # 双向各2车道
STOP_OFFSET = 90     # 停止线距路口中心距离

# 颜色（BGR）
C_ROAD    = (30, 30, 30)
C_MARKING = (200, 200, 200)
C_GRASS   = (15, 50, 15)
C_YELLOW  = (0, 180, 240)
C_WHITE   = (230, 230, 230)
C_RED_LT  = (0, 0, 220)
C_GREEN_LT= (0, 200, 60)
C_YELLOW_LT=(0, 185, 230)

VEHICLE_COLORS = {
    'car':    (180, 90, 30),
    'truck':  (50, 80, 180),
    'bus':    (30, 150, 180),
    'person': (50, 200, 200),
    'motorbike': (200, 60, 200),
}

CLASS_IDS = {'car': 0, 'truck': 1, 'bus': 2, 'motorbike': 3, 'person': 4}


class SignalPhase(IntEnum):
    NS_GREEN  = 0   # 南北直行绿灯
    NS_YELLOW = 1
    ALL_RED_1 = 2
    EW_GREEN  = 3   # 东西直行绿灯
    EW_YELLOW = 4
    ALL_RED_2 = 5


@dataclass
class Vehicle:
    vid:      int         # 唯一ID
    cls:      str         # 'car' / 'truck' / 'bus' / 'person' / 'motorbike'
    x:        float       # 中心x（像素）
    y:        float       # 中心y（像素）
    vx:       float       # 速度x（像素/帧）
    vy:       float       # 速度y（像素/帧）
    w:        int         # 宽度
    h:        int         # 高度
    lane:     int         # 车道方向（0=NS, 1=EW）
    stopped:  bool = False
    violation: bool = False  # 是否已产生违规（闯红灯）
    active:   bool = True


@dataclass
class DetectionGT:
    """场景生成器输出的 Ground Truth（用于验证检测准确率）"""
    vid:   int
    cls:   str
    x1:    int; y1: int; x2: int; y2: int
    cx:    float; cy: float


class SceneGenerator:
    def __init__(self, seed: int = 42, width: int = W, height: int = H,
                 phase_duration: dict = None):
        self.W = width
        self.H = height
        # 使用实例级RNG，避免多个生成器共享全局随机状态（保证可复现性）
        self._rng  = np.random.default_rng(seed)
        self._rand = random.Random(seed)

        self.frame_idx   = 0
        self.next_vid    = 1
        self.vehicles: List[Vehicle] = []
        self.signal_phase = SignalPhase.NS_GREEN
        self.phase_timer  = 0

        # 每个相位持续帧数（30fps 下：60帧=2s, 150帧=5s）
        self.phase_durations = phase_duration or {
            SignalPhase.NS_GREEN:  150,   # 5s 绿灯
            SignalPhase.NS_YELLOW:  36,   # 1.2s 黄灯
            SignalPhase.ALL_RED_1:  18,   # 0.6s 全红
            SignalPhase.EW_GREEN:  120,   # 4s 绿灯
            SignalPhase.EW_YELLOW:  36,
            SignalPhase.ALL_RED_2:  18,
        }

        # 生成违规事件的帧号（可复现）
        self.violation_frames = set(self._rand.sample(range(60, 600), k=5))

    # ─────────────────────────────────────────
    # 信号灯逻辑
    # ─────────────────────────────────────────
    def _update_signal(self):
        self.phase_timer += 1
        dur = self.phase_durations[self.signal_phase]
        if self.phase_timer >= dur:
            self.phase_timer = 0
            self.signal_phase = SignalPhase((self.signal_phase + 1) % len(SignalPhase))

    def is_red_for_ns(self) -> bool:
        return self.signal_phase in (SignalPhase.EW_GREEN, SignalPhase.EW_YELLOW,
                                     SignalPhase.ALL_RED_1, SignalPhase.ALL_RED_2)

    def is_red_for_ew(self) -> bool:
        return self.signal_phase in (SignalPhase.NS_GREEN, SignalPhase.NS_YELLOW,
                                     SignalPhase.ALL_RED_1, SignalPhase.ALL_RED_2)

    # ─────────────────────────────────────────
    # 车辆生成 & 移动
    # ─────────────────────────────────────────
    def _spawn_vehicle(self):
        """以一定概率生成新车"""
        if self._rand.random() > 0.08:  # 约8%概率/帧生成新车
            return
        lane = self._rand.randint(0, 1)  # 0=NS, 1=EW
        direction = self._rand.choice([-1, 1])
        cls = self._rand.choices(
            ['car', 'car', 'car', 'truck', 'bus', 'person', 'motorbike'],
            weights=[50, 50, 50, 10, 5, 15, 10])[0]

        if cls == 'person':
            w, h = 12, 28
        elif cls == 'truck':
            w, h = 28, 52
        elif cls == 'bus':
            w, h = 32, 64
        else:
            w, h = 24, 44

        spd = self._rand.uniform(2.0, 3.5) if cls != 'person' else self._rand.uniform(0.8, 1.2)
        cx = self.W // 2
        cy = self.H // 2
        offset = self._rand.choice([-LANE_W // 2, LANE_W // 2])  # 左/右车道

        if lane == 0:  # NS（垂直移动）
            x = cx + offset
            y = (self.H + h) if direction > 0 else -(h)
            vx, vy = 0.0, direction * (-spd)  # 从南向北 or 从北向南
        else:          # EW（水平移动）
            y = cy + offset
            x = (self.W + w) if direction > 0 else -(w)
            vx, vy = direction * (-spd), 0.0

        v = Vehicle(vid=self.next_vid, cls=cls, x=float(x), y=float(y),
                    vx=vx, vy=vy, w=w, h=h, lane=lane)
        self.next_vid += 1
        self.vehicles.append(v)

    def _move_vehicles(self):
        cx, cy = self.W // 2, self.H // 2
        margin = 100  # 停止线前停下来

        for v in self.vehicles:
            if not v.active:
                continue

            # 判断是否应该在停止线前停下
            if not v.violation:
                if v.lane == 0 and self.is_red_for_ns():  # NS红灯
                    stop_y_n = cy - STOP_OFFSET  # 从南行到北的停止线
                    stop_y_s = cy + STOP_OFFSET  # 从北行到南的停止线
                    if v.vy < 0 and v.y > stop_y_n and v.y - v.vy > stop_y_n:
                        v.stopped = True
                    elif v.vy > 0 and v.y < stop_y_s and v.y - v.vy < stop_y_s:
                        v.stopped = True
                elif v.lane == 1 and self.is_red_for_ew():  # EW红灯
                    stop_x_e = cx - STOP_OFFSET
                    stop_x_w = cx + STOP_OFFSET
                    if v.vx < 0 and v.x > stop_x_e and v.x - v.vx > stop_x_e:
                        v.stopped = True
                    elif v.vx > 0 and v.x < stop_x_w and v.x - v.vx < stop_x_w:
                        v.stopped = True
                else:
                    v.stopped = False  # 绿灯恢复行驶

            # 闯红灯违规（特定帧号触发）
            if self.frame_idx in self.violation_frames and not v.violation:
                if v.stopped:
                    v.violation = True
                    v.stopped = False  # 继续闯行

            if not v.stopped:
                v.x += v.vx
                v.y += v.vy

            # 超出画面，回收
            if (v.x < -100 or v.x > self.W + 100
                    or v.y < -100 or v.y > self.H + 100):
                v.active = False

        self.vehicles = [v for v in self.vehicles if v.active]

    # ─────────────────────────────────────────
    # 绘制函数
    # ─────────────────────────────────────────
    def _draw_road(self, img: np.ndarray):
        """绘制十字路口道路"""
        cx, cy = self.W // 2, self.H // 2
        hw = ROAD_W // 2

        # 草地背景
        img[:] = C_GRASS

        # 主干道（纵向 NS）
        img[:, cx - hw : cx + hw] = C_ROAD
        # 主干道（横向 EW）
        img[cy - hw : cy + hw, :] = C_ROAD
        # 路口中心框
        img[cy - hw : cy + hw, cx - hw : cx + hw] = C_ROAD

        # 停止线
        for x_off in [cx - hw, cx + hw - 2]:
            cv2.line(img, (x_off, cy - STOP_OFFSET), (x_off, cy + STOP_OFFSET),
                     C_WHITE, 2)
        for y_off in [cy - hw, cy + hw - 2]:
            cv2.line(img, (cx - STOP_OFFSET, y_off), (cx + STOP_OFFSET, y_off),
                     C_WHITE, 2)

        # 中心虚线（NS方向）
        for y in range(0, cy - hw, 20):
            cv2.line(img, (cx, y), (cx, min(y + 12, cy - hw)), C_YELLOW, 1)
        for y in range(cy + hw, self.H, 20):
            cv2.line(img, (cx, y), (cx, min(y + 12, self.H)), C_YELLOW, 1)

        # 中心虚线（EW方向）
        for x in range(0, cx - hw, 20):
            cv2.line(img, (x, cy), (min(x + 12, cx - hw), cy), C_YELLOW, 1)
        for x in range(cx + hw, self.W, 20):
            cv2.line(img, (x, cy), (min(x + 12, self.W), cy), C_YELLOW, 1)

    def _draw_traffic_lights(self, img: np.ndarray):
        """在路口四角绘制信号灯"""
        cx, cy = self.W // 2, self.H // 2
        hw = ROAD_W // 2
        positions = [
            (cx - hw - 20, cy - hw - 20),  # 西北角（EW红/绿）
            (cx + hw + 20, cy - hw - 20),  # 东北角（NS红/绿）
            (cx - hw - 20, cy + hw + 20),  # 西南角
            (cx + hw + 20, cy + hw + 20),  # 东南角
        ]
        for i, (lx, ly) in enumerate(positions):
            is_ns = (i % 2 == 1)
            red   = self.is_red_for_ns() if is_ns else self.is_red_for_ew()
            yel   = (self.signal_phase in (SignalPhase.NS_YELLOW,)
                     if is_ns else self.signal_phase == SignalPhase.EW_YELLOW)

            box_x, box_y = max(4, lx - 8), max(4, ly - 26)
            box_w, box_h = 16, 52
            cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h),
                          (20, 20, 20), -1)
            r_col = C_RED_LT    if red else (30, 0, 0)
            y_col = C_YELLOW_LT if yel else (30, 20, 0)
            g_col = C_GREEN_LT  if (not red and not yel) else (0, 30, 0)
            cv2.circle(img, (box_x + 8, box_y + 8),  5, r_col, -1)
            cv2.circle(img, (box_x + 8, box_y + 26), 5, y_col, -1)
            cv2.circle(img, (box_x + 8, box_y + 44), 5, g_col, -1)

    def _draw_vehicles(self, img: np.ndarray) -> List[DetectionGT]:
        gts = []
        for v in self.vehicles:
            if not v.active:
                continue
            x1 = int(v.x - v.w // 2)
            y1 = int(v.y - v.h // 2)
            x2 = int(v.x + v.w // 2)
            y2 = int(v.y + v.h // 2)
            # 裁剪到画面内
            x1c = max(0, x1); y1c = max(0, y1)
            x2c = min(self.W - 1, x2); y2c = min(self.H - 1, y2)
            if x2c <= x1c or y2c <= y1c:
                continue
            color = VEHICLE_COLORS.get(v.cls, (150, 150, 150))
            # 车身
            cv2.rectangle(img, (x1c, y1c), (x2c, y2c), color, -1)
            # 边框（违规车辆用红色边框）
            border_color = (0, 0, 255) if v.violation else (200, 200, 200)
            cv2.rectangle(img, (x1c, y1c), (x2c, y2c), border_color, 1)
            # 车牌（简化：白色矩形）
            if v.cls in ('car', 'truck', 'bus'):
                pw, ph = 14, 5
                px = (x1c + x2c) // 2 - pw // 2
                py = y2c - ph - 2
                if 0 <= px and px + pw < self.W and 0 <= py:
                    cv2.rectangle(img, (px, py), (px + pw, py + ph),
                                  (210, 210, 210), -1)

            gts.append(DetectionGT(
                vid=v.vid, cls=v.cls,
                x1=x1c, y1=y1c, x2=x2c, y2=y2c,
                cx=v.x, cy=v.y
            ))
        return gts

    def _draw_hud(self, img: np.ndarray):
        """绘制 HUD 信息"""
        phase_names = {
            SignalPhase.NS_GREEN:  'NS_GREEN',
            SignalPhase.NS_YELLOW: 'NS_YELLOW',
            SignalPhase.ALL_RED_1: 'ALL_RED',
            SignalPhase.EW_GREEN:  'EW_GREEN',
            SignalPhase.EW_YELLOW: 'EW_YELLOW',
            SignalPhase.ALL_RED_2: 'ALL_RED',
        }
        text = (f"Frame:{self.frame_idx:05d} "
                f"Phase:{phase_names[self.signal_phase]} "
                f"Timer:{self.phase_timer}")
        cv2.putText(img, text, (4, 16), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (200, 200, 200), 1, cv2.LINE_AA)
        veh_count = len([v for v in self.vehicles if v.active])
        cv2.putText(img, f"Vehicles:{veh_count}", (4, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 220, 180), 1)

    # ─────────────────────────────────────────
    # 主渲染函数
    # ─────────────────────────────────────────
    def next_frame(self) -> Tuple[np.ndarray, List[DetectionGT]]:
        """
        生成下一帧
        Returns:
            frame: H×W×3 BGR uint8
            gt:    该帧的 Ground Truth 检测框列表
        """
        self._update_signal()
        self._spawn_vehicle()
        self._move_vehicles()

        img = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        self._draw_road(img)
        self._draw_traffic_lights(img)
        gt = self._draw_vehicles(img)
        self._draw_hud(img)

        # 添加轻微噪声模拟真实摄像头（使用实例RNG保证可复现）
        noise = self._rng.integers(-8, 8, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        self.frame_idx += 1
        return img, gt

    def get_signal_state(self) -> dict:
        return {
            'phase': self.signal_phase.name,
            'phase_id': int(self.signal_phase),
            'timer': self.phase_timer,
            'ns_red': self.is_red_for_ns(),
            'ew_red': self.is_red_for_ew(),
            'remain_frames': self.phase_durations[self.signal_phase] - self.phase_timer,
        }


if __name__ == '__main__':
    gen = SceneGenerator(seed=42)
    print("场景生成器自测（生成100帧，保存预览）")
    for i in range(100):
        frame, gt = gen.next_frame()
        if i % 30 == 0:
            fname = f'/tmp/sim_frame_{i:03d}.jpg'
            cv2.imwrite(fname, frame)
            print(f"  帧 {i:03d}: {len(gt)} 目标, 信号={gen.get_signal_state()['phase']}, 保存: {fname}")
    print("✓ 场景生成器正常")
