#pragma once
#include "inference_engine.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <functional>
#include <opencv2/core.hpp>

enum class EventType {
    RED_LIGHT_VIOLATION,   // 闯红灯
    WRONG_WAY_DRIVING,     // 逆行
    ILLEGAL_PARKING,       // 违规停车（超过30s静止）
    PEDESTRIAN_JAYWALKING, // 行人闯红灯
    CONGESTION_DETECTED,   // 拥堵（排队长度超阈值）
    OVERSIZED_VEHICLE,     // 大型车辆（高/宽超限）
};

struct TrafficEvent {
    EventType   type;
    std::string plate;      // 涉事车牌（如有）
    uint8_t     track_id;
    uint8_t     channel;
    uint64_t    timestamp_us;
    cv::Point2f location;   // 事件发生像素坐标
    float       severity;   // 严重程度 0-1
    std::string description;
};

// 检测区域配置（从配置文件加载）
struct RuleConfig {
    // 各方向停车线（多边形顶点列表）
    std::vector<cv::Point2f> stop_line_ns;  // 南北方向停车线
    std::vector<cv::Point2f> stop_line_ew;  // 东西方向停车线
    // 人行横道区域
    std::vector<cv::Point2f> crosswalk;
    // 行车方向（各通道的期望运动方向角度，0=右, 90=下, 180=左, 270=上）
    float expected_direction_deg[4]{270, 90, 0, 180};
    // 排队长度阈值（超过则触发拥堵事件）
    float congestion_queue_m{50.f};
    // 像素到米的比例（需要标定）
    float pixel_to_meter{0.05f};  // 1像素 = 5cm（1080p，典型路口高度）
};

class EventDetector {
public:
    using EventCallback = std::function<void(const TrafficEvent&,
                                             std::shared_ptr<VideoFrame>)>;

    explicit EventDetector(const RuleConfig& rules);

    // 输入推理结果 + 当前信号状态，输出触发的事件列表
    std::vector<TrafficEvent> detect(
        const FrameResult& result,
        bool signal_is_red,              // 当前是否红灯
        std::shared_ptr<VideoFrame> frame // 用于截图证据
    );

    // 注册事件回调（异步通知）
    void set_callback(EventCallback cb) { callback_ = std::move(cb); }

    // 获取各方向当前排队长度（米）
    float get_queue_length_m(int channel) const;

private:
    RuleConfig rules_;
    EventCallback callback_;

    // 历史轨迹（用于逆行/停车检测）
    struct TrackHistory {
        std::vector<cv::Point2f> positions;  // 最近 30 帧位置
        uint64_t first_seen_us{0};
        uint64_t last_moved_us{0};
        bool violation_reported{false};
    };
    std::unordered_map<int, TrackHistory> tracks_;  // track_id → 历史

    // 内部检测函数
    bool check_red_light(const DetectedObject& obj, bool red, int ch) const;
    bool check_wrong_way(const DetectedObject& obj, int ch);
    bool check_parking(const DetectedObject& obj, uint64_t ts_us);
    void update_queue_length(const FrameResult& result);

    // 线段交叉检测
    static bool line_segments_cross(cv::Point2f p1, cv::Point2f p2,
                                    cv::Point2f p3, cv::Point2f p4);

    float queue_length_m_[4]{};  // 各通道排队长度
};
