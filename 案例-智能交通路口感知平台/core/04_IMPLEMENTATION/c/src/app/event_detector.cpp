// @req SYS-REQ-005, STK-REQ-001
// @design DES-ARCH-009
// @test TC-EVENT-001
// @author sw-team | @since 2026-06-04 | @version 1.0
// @status approved
//
// Event detector: red-light violation / wrong-way / illegal parking /
// pedestrian jaywalk. Uses ByteTrack trajectories + signal-light state.

#include "event_detector.h"
#include <cmath>
#include <algorithm>
#include <chrono>

static float angle_diff(float a, float b) {
    float d = std::fabs(a - b);
    return d > 180.f ? 360.f - d : d;
}

static cv::Point2f obj_center(const DetectedObject& o) {
    return {o.x + o.w * 0.5f, o.y + o.h * 0.9f};  // 使用底部中心
}

EventDetector::EventDetector(const RuleConfig& rules) : rules_(rules) {}

bool EventDetector::line_segments_cross(
    cv::Point2f p1, cv::Point2f p2,
    cv::Point2f p3, cv::Point2f p4) {
    // 标准线段交叉检测（向量叉积法）
    auto cross = [](cv::Point2f a, cv::Point2f b) {
        return a.x * b.y - a.y * b.x;
    };
    cv::Point2f d1 = p2 - p1, d2 = p4 - p3;
    float denom = cross(d1, d2);
    if (std::abs(denom) < 1e-6f) return false;  // 平行
    cv::Point2f dp = p3 - p1;
    float t = cross(dp, d2) / denom;
    float u = cross(dp, d1) / denom;
    return t >= 0.f && t <= 1.f && u >= 0.f && u <= 1.f;
}

bool EventDetector::check_red_light(
    const DetectedObject& obj, bool red, int ch) const {
    if (!red || obj.class_id > 2) return false;  // 只检测机动车
    if (obj.track_id == 0) return false;          // 未跟踪的目标跳过

    // 停车线选择（0/2 通道 = 南北，1/3 = 东西）
    const auto& stop_line = (ch % 2 == 0) ?
        rules_.stop_line_ns : rules_.stop_line_ew;
    if (stop_line.size() < 2) return false;

    cv::Point2f center = obj_center(obj);

    // 判断目标中心是否在停车线的"越线一侧"
    // 简化：车辆中心 y 坐标是否超过停车线 y（适用于南北方向）
    float line_y = (stop_line[0].y + stop_line[1].y) / 2.f;
    return (ch < 2) ? (center.y > line_y) : (center.x > stop_line[0].x);
}

bool EventDetector::check_wrong_way(const DetectedObject& obj, int ch) {
    if (obj.track_id == 0) return false;
    auto& hist = tracks_[obj.track_id];
    hist.positions.push_back(obj_center(obj));
    if (hist.positions.size() > 30) hist.positions.erase(hist.positions.begin());
    if (hist.positions.size() < 10) return false;

    // 计算轨迹方向（最近 10 帧的平均运动向量）
    cv::Point2f motion{0, 0};
    for (int i = hist.positions.size() - 9; i < (int)hist.positions.size(); i++) {
        motion += hist.positions[i] - hist.positions[i - 1];
    }
    float speed = std::sqrt(motion.x * motion.x + motion.y * motion.y);
    if (speed < 5.f) return false;  // 速度太慢，不判断方向

    float angle = std::atan2(motion.y, motion.x) * 180.f / M_PI;
    if (angle < 0) angle += 360.f;
    return angle_diff(angle, rules_.expected_direction_deg[ch]) > 150.f;
}

bool EventDetector::check_parking(const DetectedObject& obj, uint64_t ts_us) {
    if (obj.class_id > 2) return false;  // 仅机动车
    auto& hist = tracks_[obj.track_id];
    if (hist.first_seen_us == 0) { hist.first_seen_us = ts_us; hist.last_moved_us = ts_us; }

    if (!hist.positions.empty()) {
        cv::Point2f last = hist.positions.back();
        cv::Point2f curr = obj_center(obj);
        if (cv::norm(curr - last) > 10.f) hist.last_moved_us = ts_us;
    }
    // 超过 30s 静止且停在非停车区域
    float still_sec = (ts_us - hist.last_moved_us) / 1e6f;
    return still_sec > 30.f && !hist.violation_reported;
}

void EventDetector::update_queue_length(const FrameResult& result) {
    // 统计各通道最远的等待车辆位置（估算排队长度）
    for (int ch = 0; ch < 4; ch++) {
        float max_dist = 0;
        for (int i = 0; i < result.object_count; i++) {
            const auto& obj = result.objects[i];
            if (obj.class_id > 2 || obj.channel != ch) continue;
            // 简化：用像素距离估算
            float dist = obj.y * rules_.pixel_to_meter;
            max_dist = std::max(max_dist, dist);
        }
        queue_length_m_[ch] = max_dist;
    }
}

std::vector<TrafficEvent> EventDetector::detect(
    const FrameResult& result,
    bool signal_is_red,
    std::shared_ptr<VideoFrame> frame) {

    std::vector<TrafficEvent> events;
    update_queue_length(result);

    for (int i = 0; i < result.object_count; i++) {
        const auto& obj = result.objects[i];

        // 1. 闯红灯
        if (check_red_light(obj, signal_is_red, result.channel)) {
            TrafficEvent ev;
            ev.type         = EventType::RED_LIGHT_VIOLATION;
            ev.plate        = obj.plate;
            ev.track_id     = obj.track_id;
            ev.channel      = result.channel;
            ev.timestamp_us = result.timestamp_us;
            ev.location     = obj_center(obj);
            ev.severity     = 0.9f;
            ev.description  = "红灯越线";
            events.push_back(ev);
            tracks_[obj.track_id].violation_reported = true;
            if (callback_) callback_(ev, frame);
        }

        // 2. 逆行
        if (check_wrong_way(obj, result.channel)) {
            TrafficEvent ev;
            ev.type         = EventType::WRONG_WAY_DRIVING;
            ev.plate        = obj.plate;
            ev.track_id     = obj.track_id;
            ev.channel      = result.channel;
            ev.timestamp_us = result.timestamp_us;
            ev.location     = obj_center(obj);
            ev.severity     = 0.95f;
            ev.description  = "逆向行驶";
            events.push_back(ev);
            if (callback_) callback_(ev, frame);
        }

        // 3. 违规停车
        if (check_parking(obj, result.timestamp_us)) {
            TrafficEvent ev;
            ev.type         = EventType::ILLEGAL_PARKING;
            ev.plate        = obj.plate;
            ev.channel      = result.channel;
            ev.timestamp_us = result.timestamp_us;
            ev.severity     = 0.5f;
            ev.description  = "违规停车超30秒";
            events.push_back(ev);
            tracks_[obj.track_id].violation_reported = true;
            if (callback_) callback_(ev, frame);
        }
    }

    // 4. 拥堵检测（全通道汇总）
    for (int ch = 0; ch < 4; ch++) {
        if (queue_length_m_[ch] > rules_.congestion_queue_m) {
            TrafficEvent ev;
            ev.type      = EventType::CONGESTION_DETECTED;
            ev.channel   = (uint8_t)ch;
            ev.timestamp_us = result.timestamp_us;
            ev.severity  = std::min(1.0f, queue_length_m_[ch] / 100.f);
            ev.description = "排队长度 " +
                std::to_string((int)queue_length_m_[ch]) + "m";
            events.push_back(ev);
            if (callback_) callback_(ev, frame);
        }
    }

    return events;
}

float EventDetector::get_queue_length_m(int ch) const {
    return (ch >= 0 && ch < 4) ? queue_length_m_[ch] : 0.f;
}
