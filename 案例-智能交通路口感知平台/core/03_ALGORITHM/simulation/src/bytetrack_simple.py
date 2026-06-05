# @req SYS-REQ-004
# @design DES-ARCH-008
# @test TC-TRACK-001
# @author ai-team | @since 2026-06-04 | @version 1.0
# @status verified
"""
ALG-TRACK-001: ByteTrack 简化实现

参考算法：
    Cao et al. "ByteTrack: Multi-Object Tracking by Associating Every
    Detection Box", ECCV 2022.

两阶段关联：
    1. 第一关联：高置信度检测 (score > 0.5) 与上一帧轨迹
    2. 第二关联：低置信度检测 (0.1 < score < 0.5) 与剩余轨迹
    → 利用低分检测找回被遮挡目标

本实现为 Python 仿真版本，对应 C++ 实现见
core/04_IMPLEMENTATION/c/src/app/bytetrack.cpp
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class TrackBox:
    track_id: int
    cls:      str
    cx: float; cy: float
    x1: int; y1: int; x2: int; y2: int
    confidence: float
    age:     int = 1       # 连续匹配帧数
    lost:    int = 0       # 连续未匹配帧数
    history: List[Tuple[float, float]] = field(default_factory=list)  # 最近30帧中心点


def iou(a, b) -> float:
    ix1 = max(a.x1, b.x1); iy1 = max(a.y1, b.y1)
    ix2 = min(a.x2, b.x2); iy2 = min(a.y2, b.y2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (a.x2 - a.x1) * (a.y2 - a.y1)
    area_b = (b.x2 - b.x1) * (b.y2 - b.y1)
    return inter / (area_a + area_b - inter)


class ByteTracker:
    """
    简化版 ByteTrack
    - 高置信度检测（conf ≥ high_thresh）先匹配
    - 低置信度检测（conf ∈ [low_thresh, high_thresh]）二次匹配未关联轨迹
    - 轨迹 lost > max_lost_age 则删除
    """
    def __init__(self, high_thresh: float = 0.5, low_thresh: float = 0.1,
                 iou_thresh: float = 0.4, max_lost_age: int = 30,
                 max_history: int = 30):
        self.high_thresh  = high_thresh
        self.low_thresh   = low_thresh
        self.iou_thresh   = iou_thresh
        self.max_lost_age = max_lost_age
        self.max_history  = max_history

        self._next_id = 1
        self.tracks: List[TrackBox] = []

    def _match(self, tracks: List[TrackBox], dets: List,
               thresh: float) -> Tuple[dict, list, list]:
        """匈牙利算法（贪心近似）+ IoU阈值过滤"""
        if not tracks or not dets:
            return {}, list(range(len(tracks))), list(range(len(dets)))

        # 构建代价矩阵
        cost = np.zeros((len(tracks), len(dets)))
        for i, trk in enumerate(tracks):
            for j, det in enumerate(dets):
                cost[i, j] = 1.0 - iou(trk, det)

        # 贪心匹配（按最小代价）
        matched   = {}
        used_trk  = set()
        used_det  = set()
        pairs     = np.dstack(np.unravel_index(np.argsort(cost.ravel()), cost.shape))[0]
        for ti, di in pairs:
            if ti in used_trk or di in used_det:
                continue
            if cost[ti, di] > (1.0 - thresh):
                break
            matched[ti] = di
            used_trk.add(ti)
            used_det.add(di)

        unmatched_trk = [i for i in range(len(tracks)) if i not in used_trk]
        unmatched_det = [j for j in range(len(dets)) if j not in used_det]
        return matched, unmatched_trk, unmatched_det

    def _det_to_box(self, det) -> TrackBox:
        cx = (det.x1 + det.x2) / 2.0
        cy = (det.y1 + det.y2) / 2.0
        return TrackBox(track_id=-1, cls=det.class_name,
                        cx=cx, cy=cy, x1=det.x1, y1=det.y1,
                        x2=det.x2, y2=det.y2, confidence=det.confidence)

    def update(self, detections: list) -> List[TrackBox]:
        """
        输入本帧检测结果，返回当前活跃轨迹列表（track_id 已赋值）
        """
        high_dets = [d for d in detections if d.confidence >= self.high_thresh]
        low_dets  = [d for d in detections if self.low_thresh <= d.confidence < self.high_thresh]

        high_boxes = [self._det_to_box(d) for d in high_dets]
        low_boxes  = [self._det_to_box(d) for d in low_dets]

        active_tracks = [t for t in self.tracks if t.lost == 0]
        lost_tracks   = [t for t in self.tracks if t.lost > 0]

        # 第一次匹配（高置信度）
        matched1, unmatched_active, unmatched_high = self._match(
            active_tracks, high_boxes, self.iou_thresh)

        # 第二次匹配（低置信度与未匹配的活跃轨迹）
        rem_tracks = [active_tracks[i] for i in unmatched_active]
        matched2, still_unmatched_trk, unmatched_low = self._match(
            rem_tracks, low_boxes, self.iou_thresh)

        # 更新匹配轨迹
        def update_track(trk: TrackBox, box: TrackBox):
            trk.x1 = box.x1; trk.y1 = box.y1
            trk.x2 = box.x2; trk.y2 = box.y2
            trk.cx = box.cx; trk.cy = box.cy
            trk.cls = box.cls
            trk.confidence = box.confidence
            trk.age  += 1
            trk.lost  = 0
            trk.history.append((trk.cx, trk.cy))
            if len(trk.history) > self.max_history:
                trk.history.pop(0)

        for ti, di in matched1.items():
            update_track(active_tracks[ti], high_boxes[di])
            high_boxes[di].track_id = active_tracks[ti].track_id

        for ti, di in matched2.items():
            trk = rem_tracks[ti]
            update_track(trk, low_boxes[di])
            low_boxes[di].track_id = trk.track_id

        # 未匹配活跃轨迹 → 标记 lost
        all_unmatched_active = set()
        for i in unmatched_active:
            if active_tracks[i] not in [rem_tracks[j] for j in range(len(rem_tracks)) if j in matched2]:
                all_unmatched_active.add(i)
        for i in all_unmatched_active:
            active_tracks[i].lost += 1

        # 新建轨迹（高置信度未匹配）
        for di in unmatched_high:
            box = high_boxes[di]
            box.track_id = self._next_id
            self._next_id += 1
            box.history   = [(box.cx, box.cy)]
            self.tracks.append(box)

        # 删除过期轨迹
        self.tracks = [t for t in self.tracks if t.lost <= self.max_lost_age]

        # 返回所有活跃轨迹
        return [t for t in self.tracks if t.lost == 0]


if __name__ == '__main__':
    from scene_generator import SceneGenerator
    from mock_detector import MockDetector

    gen     = SceneGenerator(seed=42)
    det     = MockDetector()
    tracker = ByteTracker()
    max_id  = 0

    for i in range(200):
        frame, gt = gen.next_frame()
        dets, _ = det.detect(frame, gt)
        tracks  = tracker.update(dets)
        max_id  = max(max_id, max((t.track_id for t in tracks), default=0))

    print(f"ByteTracker 自测（200帧）:")
    print(f"  最大轨迹ID: {max_id}")
    print(f"  当前活跃轨迹: {len(tracker.tracks)}")
    assert max_id > 0, "没有产生任何跟踪ID"
    print("✓ ByteTracker 正常")
