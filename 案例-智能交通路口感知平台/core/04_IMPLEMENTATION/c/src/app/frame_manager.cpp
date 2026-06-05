// @req SYS-REQ-001, PERF-REQ-001
// @design DES-ARCH-004
// @test TC-CAM-001, TC-PERF-LAT-001
// @author sw-team | @since 2026-06-04 | @version 1.0
// @status verified
//
// Zero-copy frame buffer manager: 3-frame circular queue per channel,
// mmap() of VDMA physical address. NV12 → BGR lazy conversion for
// preview; JPEG encoding for evidence on demand.

#include "frame_manager.h"
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdexcept>
#include <cstring>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <chrono>

// ── VideoFrame 实现 ────────────────────────────────────────
const cv::Mat& VideoFrame::get_preview() {
    if (!preview_ready) {
        // NV12 → BGR（全分辨率）
        cv::Mat yuv(height * 3 / 2, width, CV_8UC1, data_nv12);
        cv::Mat bgr_full;
        cv::cvtColor(yuv, bgr_full, cv::COLOR_YUV2BGR_NV12);
        // 缩小到 1/4 用于预览
        cv::resize(bgr_full, bgr_preview,
                   cv::Size(width / 4, height / 4),
                   0, 0, cv::INTER_AREA);
        preview_ready = true;
    }
    return bgr_preview;
}

std::vector<uint8_t> VideoFrame::to_jpeg(int quality) const {
    // 原始分辨率的 JPEG（用于违规证据）
    cv::Mat yuv(height * 3 / 2, width, CV_8UC1, data_nv12);
    cv::Mat bgr;
    cv::cvtColor(yuv, bgr, cv::COLOR_YUV2BGR_NV12);
    // 缩到 1080p 以节省带宽
    if (width > 1920) cv::resize(bgr, bgr, cv::Size(1920, 1080));
    std::vector<uint8_t> jpeg;
    cv::imencode(".jpg", bgr, jpeg, {cv::IMWRITE_JPEG_QUALITY, quality});
    return jpeg;
}

// ── ChannelBuffer 实现 ─────────────────────────────────────
ChannelBuffer::ChannelBuffer(int ch, uint8_t* base_addr, size_t frame_size)
    : channel_(ch), base_addr_(base_addr), frame_size_(frame_size) {
    for (int i = 0; i < NUM_BUFS; i++) {
        slots_[i].ptr = base_addr + i * frame_size;
        slots_[i].ready = false;
    }
}

void ChannelBuffer::mark_ready(int buf_idx, uint64_t ts_us, uint32_t frame_id) {
    std::lock_guard<std::mutex> lk(mtx_);
    slots_[buf_idx].ready      = true;
    slots_[buf_idx].timestamp_us = ts_us;
    slots_[buf_idx].frame_id   = frame_id;
    // 构造 VideoFrame（共享指针管理生命周期）
    auto frame = std::make_shared<VideoFrame>();
    frame->channel      = channel_;
    frame->frame_id     = frame_id;
    frame->timestamp_us = ts_us;
    frame->data_nv12    = slots_[buf_idx].ptr;
    frame->size         = frame_size_;
    frame->width        = 1920;
    frame->height       = 1080;
    if (latest_) drop_count_++;  // 上一帧还未被消费
    latest_ = frame;
    cv_.notify_one();
}

std::shared_ptr<VideoFrame> ChannelBuffer::pop(int timeout_ms) {
    std::unique_lock<std::mutex> lk(mtx_);
    if (!cv_.wait_for(lk, std::chrono::milliseconds(timeout_ms),
                      [this] { return latest_ != nullptr; })) {
        return nullptr;  // 超时
    }
    return std::move(latest_);
}

std::shared_ptr<VideoFrame> ChannelBuffer::try_pop() {
    std::lock_guard<std::mutex> lk(mtx_);
    return std::move(latest_);
}

std::shared_ptr<VideoFrame> ChannelBuffer::peek_latest() {
    std::lock_guard<std::mutex> lk(mtx_);
    return latest_;
}

// ── FrameManager 实现 ──────────────────────────────────────
FrameManager::FrameManager(int num_channels) : num_channels_(num_channels) {
    // 映射物理内存（视频帧缓冲区在 reserved-memory 中）
    mem_fd_ = open("/dev/mem", O_RDWR | O_SYNC);
    if (mem_fd_ < 0) throw std::runtime_error("Cannot open /dev/mem");

    size_t total = num_channels * ChannelBuffer::NUM_BUFS * FRAME_SIZE;
    mem_base_ = (uint8_t*)mmap(nullptr, total,
                               PROT_READ | PROT_WRITE, MAP_SHARED,
                               mem_fd_, VBUF_BASE);
    if (mem_base_ == MAP_FAILED)
        throw std::runtime_error("mmap failed for video buffer");

    // 为每个通道创建缓冲管理器
    for (int ch = 0; ch < num_channels; ch++) {
        uint8_t* ch_base = mem_base_ + ch * ChannelBuffer::NUM_BUFS * FRAME_SIZE;
        channels_.emplace_back(
            std::make_unique<ChannelBuffer>(ch, ch_base, FRAME_SIZE));
    }
}

FrameManager::~FrameManager() {
    if (mem_base_ && mem_base_ != MAP_FAILED) {
        munmap(mem_base_, num_channels_ * ChannelBuffer::NUM_BUFS * FRAME_SIZE);
    }
    if (mem_fd_ >= 0) close(mem_fd_);
}

void FrameManager::push(int ch, uint8_t* data, uint64_t ts_us, uint32_t fid) {
    if (ch < 0 || ch >= num_channels_) return;
    // 找到对应的缓冲槽
    int buf_idx = (int)((data - channels_[ch]->base_addr_) / FRAME_SIZE);
    channels_[ch]->mark_ready(buf_idx, ts_us, fid);
}

std::shared_ptr<VideoFrame> FrameManager::pop(int ch, int timeout_ms) {
    if (ch < 0 || ch >= num_channels_) return nullptr;
    return channels_[ch]->pop(timeout_ms);
}

std::shared_ptr<VideoFrame> FrameManager::get_latest(int ch) {
    if (ch < 0 || ch >= num_channels_) return nullptr;
    return channels_[ch]->peek_latest();
}

void FrameManager::print_stats() const {
    for (int ch = 0; ch < num_channels_; ch++) {
        printf("Channel %d: drops=%lu\n",
               ch, channels_[ch]->get_drop_count());
    }
}
