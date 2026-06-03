#pragma once
#include "frame_manager.h"
#include <vitis/ai/yolov8.hpp>
#include <vitis/ai/lprnet.hpp>
#include <memory>
#include <string>
#include <cstdint>

// 单个检测对象（与 R5 共享内存结构对齐）
struct DetectedObject {
    uint8_t  class_id;      // 0=car 1=truck 2=bus 3=person 4=motorcycle 5=bicycle
    uint8_t  confidence;    // 0-100
    uint8_t  track_id;      // ByteTrack 分配的跟踪 ID
    uint8_t  flags;         // bit0:有车牌 bit1:违规
    uint16_t x, y, w, h;   // 像素坐标（相对于 DST_WIDTH × DST_HEIGHT）
    char     plate[12];     // 车牌号（仅机动车，空则全0）
    float    speed_kmh;     // 估算速度（-1 表示未知）
};

// 单帧推理结果
struct FrameResult {
    uint8_t  channel;
    uint32_t frame_id;
    uint64_t timestamp_us;
    int      object_count;
    DetectedObject objects[64];
};

// DPU 推理引擎（封装 Vitis AI VART）
class InferenceEngine {
public:
    struct Config {
        std::string yolo_model_path{"/opt/models/yolov8s_traffic.xmodel"};
        std::string lpr_model_path {"/opt/models/lprnet.xmodel"};
        float       yolo_conf_thresh{0.40f};
        float       yolo_nms_thresh {0.50f};
        float       lpr_conf_thresh {0.80f};
        bool        enable_lpr{true};   // 是否启用车牌识别
        int         lpr_min_box_area{400};  // 最小检测框面积（像素²）才触发 LPR
    };

    explicit InferenceEngine(const Config& cfg = {});
    ~InferenceEngine() = default;

    // 主推理接口：输入 NV12 帧，输出检测结果
    FrameResult run(const VideoFrame& frame);

    // 批量推理（多帧并行，提高 DPU 利用率）
    std::vector<FrameResult> run_batch(
        const std::vector<std::shared_ptr<VideoFrame>>& frames);

    // 获取 DPU 利用率统计
    float get_dpu_utilization() const;
    double get_avg_latency_ms() const;

private:
    Config cfg_;
    std::unique_ptr<vitis::ai::YOLOv8>  yolo_;
    std::unique_ptr<vitis::ai::LPRNet>  lpr_;

    // 性能统计
    mutable std::mutex stats_mtx_;
    uint64_t total_frames_{0};
    double   total_latency_ms_{0};

    // 内部辅助
    cv::Mat  nv12_to_bgr(const VideoFrame& frame) const;
    void     run_lpr(const cv::Mat& bgr, DetectedObject& obj) const;
    cv::Rect safe_roi(const cv::Mat& img, int x, int y, int w, int h) const;
};
