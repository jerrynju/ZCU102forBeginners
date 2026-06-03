#include "inference_engine.h"
#include <opencv2/imgproc.hpp>
#include <chrono>
#include <cstring>
#include <algorithm>
#include <stdexcept>

InferenceEngine::InferenceEngine(const Config& cfg) : cfg_(cfg) {
    // 加载 YOLOv8 xmodel
    yolo_ = vitis::ai::YOLOv8::create(cfg_.yolo_model_path, true);
    if (!yolo_) throw std::runtime_error("Failed to load YOLOv8 xmodel: " + cfg_.yolo_model_path);

    if (cfg_.enable_lpr) {
        lpr_ = vitis::ai::LPRNet::create(cfg_.lpr_model_path, true);
        if (!lpr_) throw std::runtime_error("Failed to load LPRNet xmodel: " + cfg_.lpr_model_path);
    }
}

cv::Mat InferenceEngine::nv12_to_bgr(const VideoFrame& frame) const {
    cv::Mat yuv(frame.height * 3 / 2, frame.width, CV_8UC1, frame.data_nv12);
    cv::Mat bgr;
    cv::cvtColor(yuv, bgr, cv::COLOR_YUV2BGR_NV12);
    return bgr;
}

cv::Rect InferenceEngine::safe_roi(const cv::Mat& img, int x, int y, int w, int h) const {
    x = std::max(0, x);
    y = std::max(0, y);
    w = std::min(w, img.cols - x);
    h = std::min(h, img.rows - y);
    return cv::Rect(x, y, std::max(1, w), std::max(1, h));
}

void InferenceEngine::run_lpr(const cv::Mat& bgr, DetectedObject& obj) const {
    if (!lpr_ || obj.class_id > 2) return;  // 仅对机动车跑 LPR

    // 在检测框下 60% 区域内寻找车牌
    int px = obj.x, py = obj.y + obj.h * 0.4, pw = obj.w, ph = obj.h * 0.6;
    cv::Rect roi = safe_roi(bgr, px, py, pw, ph);
    if (roi.area() < cfg_.lpr_min_box_area) return;

    cv::Mat plate_crop = bgr(roi);
    cv::resize(plate_crop, plate_crop, cv::Size(96, 24));

    auto result = lpr_->run(plate_crop);
    if (!result.plate_number.empty()) {
        strncpy(obj.plate, result.plate_number.c_str(), sizeof(obj.plate) - 1);
        obj.flags |= 0x01;  // 标记有车牌
    }
}

FrameResult InferenceEngine::run(const VideoFrame& frame) {
    auto t0 = std::chrono::steady_clock::now();

    // NV12 → BGR（DPU 需要 BGR 格式）
    cv::Mat bgr = nv12_to_bgr(frame);

    // YOLOv8 推理
    auto yolo_result = yolo_->run(bgr);

    // 构建输出结果
    FrameResult result{};
    result.channel      = frame.channel;
    result.frame_id     = frame.frame_id;
    result.timestamp_us = frame.timestamp_us;
    result.object_count = 0;

    for (const auto& box : yolo_result.bboxes) {
        if (box.score < cfg_.yolo_conf_thresh) continue;
        if (result.object_count >= 64) break;

        auto& obj = result.objects[result.object_count++];
        obj.class_id   = (uint8_t)box.label;
        obj.confidence = (uint8_t)(box.score * 100);
        obj.x = (uint16_t)(box.x      * frame.width);
        obj.y = (uint16_t)(box.y      * frame.height);
        obj.w = (uint16_t)(box.width  * frame.width);
        obj.h = (uint16_t)(box.height * frame.height);
        obj.speed_kmh = -1.f;
        memset(obj.plate, 0, sizeof(obj.plate));
        obj.flags = 0;

        // 车牌识别（仅机动车）
        run_lpr(bgr, obj);
    }

    auto t1 = std::chrono::steady_clock::now();
    double latency = std::chrono::duration<double, std::milli>(t1 - t0).count();

    std::lock_guard<std::mutex> lk(stats_mtx_);
    total_frames_++;
    total_latency_ms_ += latency;

    return result;
}

std::vector<FrameResult> InferenceEngine::run_batch(
    const std::vector<std::shared_ptr<VideoFrame>>& frames) {
    std::vector<FrameResult> results;
    results.reserve(frames.size());
    for (const auto& f : frames) {
        if (f) results.push_back(run(*f));
    }
    return results;
}

double InferenceEngine::get_avg_latency_ms() const {
    std::lock_guard<std::mutex> lk(stats_mtx_);
    return total_frames_ > 0 ? total_latency_ms_ / total_frames_ : 0.0;
}
