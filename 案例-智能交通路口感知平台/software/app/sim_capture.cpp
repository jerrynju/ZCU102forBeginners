#include "sim_capture.h"
#include <cstring>
#include <cmath>
#include <chrono>
#include <stdexcept>
#include <cstdio>

// ─────────────────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────────────────
static uint64_t now_us() {
    using namespace std::chrono;
    return duration_cast<microseconds>(
        steady_clock::now().time_since_epoch()).count();
}

// BGR → NV12 逐像素（用于生成测试图案）
static void bgr_to_nv12(const uint8_t* bgr, uint8_t* nv12, int w, int h) {
    uint8_t* Y   = nv12;
    uint8_t* UV  = nv12 + w * h;
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            const uint8_t* p = bgr + (y * w + x) * 3;
            uint8_t B = p[0], G = p[1], R = p[2];
            // BT.601 全范围
            int Yv = (( 66*R + 129*G +  25*B + 128) >> 8) + 16;
            Y[y * w + x] = (uint8_t)std::max(0, std::min(255, Yv));
        }
    }
    for (int y = 0; y < h; y += 2) {
        for (int x = 0; x < w; x += 2) {
            const uint8_t* p = bgr + (y * w + x) * 3;
            uint8_t B = p[0], G = p[1], R = p[2];
            int Uv = ((-38*R -  74*G + 112*B + 128) >> 8) + 128;
            int Vv = ((112*R -  94*G -  18*B + 128) >> 8) + 128;
            int ui = (y / 2) * w + x;
            UV[ui]   = (uint8_t)std::max(0, std::min(255, Uv));
            UV[ui+1] = (uint8_t)std::max(0, std::min(255, Vv));
        }
    }
}

// ─────────────────────────────────────────────────────────
// SimFrameSource
// ─────────────────────────────────────────────────────────
SimFrameSource::SimFrameSource(int channel, const std::string& video_path)
    : channel_(channel), video_path_(video_path) {

    if (!video_path.empty()) {
        // 尝试用 OpenCV 打开视频文件（动态链接，避免强依赖）
#ifdef HAVE_OPENCV_VIDEO
        auto* cap = new cv::VideoCapture(video_path);
        if (cap->isOpened()) {
            cap_ = cap;
            open_ = true;
            return;
        }
        delete cap;
#endif
        fprintf(stderr, "[SimCapture] 无法打开视频文件 %s，使用合成图案\n",
                video_path.c_str());
    }
    open_ = true;  // 合成模式始终可用
}

SimFrameSource::~SimFrameSource() {
#ifdef HAVE_OPENCV_VIDEO
    if (cap_) {
        delete reinterpret_cast<cv::VideoCapture*>(cap_);
        cap_ = nullptr;
    }
#endif
}

void SimFrameSource::fill_nv12_pattern(uint8_t* buf, uint32_t fid) const {
    // 分配临时 BGR 缓冲
    static thread_local std::vector<uint8_t> bgr_buf(SIM_W * SIM_H * 3, 0);

    // 深色背景（路面）
    std::fill(bgr_buf.begin(), bgr_buf.end(), 25);

    // 水平道路标线
    auto draw_hline = [&](int y, int x0, int x1, uint8_t r, uint8_t g, uint8_t b) {
        for (int x = x0; x < x1 && x < SIM_W; x++) {
            auto* p = bgr_buf.data() + (y * SIM_W + x) * 3;
            p[0] = b; p[1] = g; p[2] = r;
        }
    };

    // 中心线
    for (int y = SIM_H / 2 - 2; y <= SIM_H / 2 + 2; y++)
        draw_hline(y, 0, SIM_W, 180, 180, 0);  // 黄色

    // 路侧白线
    for (int y = 20; y < SIM_H - 20; y++) {
        draw_hline(y, 10, 15, 200, 200, 200);
        draw_hline(y, SIM_W - 15, SIM_W - 10, 200, 200, 200);
    }

    // 移动目标方块（模拟 4 辆车，不同通道不同初始位置）
    const int NUM_BOXES = 4;
    const int BOX_W = 80, BOX_H = 50;
    const uint8_t colors[4][3] = {
        {180,  80,  40},   // 蓝色车
        { 40, 160,  60},   // 绿色车
        {200,  80, 180},   // 紫色车
        { 80, 200, 200},   // 青色车
    };

    for (int b = 0; b < NUM_BOXES; b++) {
        int period = 300 + b * 50;
        int phase  = (fid + b * (period / NUM_BOXES)) % period;
        int bx = (int)(((float)phase / period) * (SIM_W - BOX_W));
        int by = SIM_H / 4 + b * (SIM_H / 5) + channel_ * 8;
        bx = std::max(0, std::min(bx, SIM_W - BOX_W));
        by = std::max(0, std::min(by, SIM_H - BOX_H));

        for (int dy = 0; dy < BOX_H; dy++) {
            for (int dx = 0; dx < BOX_W; dx++) {
                auto* p = bgr_buf.data() + ((by + dy) * SIM_W + (bx + dx)) * 3;
                p[0] = colors[b][2]; p[1] = colors[b][1]; p[2] = colors[b][0];
            }
        }
    }

    // 帧号信息（顶部浅色数字条，方便肉眼验证帧序列）
    uint8_t lum = (uint8_t)((fid % 100) * 2 + 55);
    for (int x = 0; x < (int)(fid % SIM_W); x++) {
        auto* p = bgr_buf.data() + x * 3;
        p[0] = p[1] = p[2] = lum;
    }

    bgr_to_nv12(bgr_buf.data(), buf, SIM_W, SIM_H);
}

void SimFrameSource::generate_frame(uint8_t* buf, uint32_t frame_id) const {
#ifdef HAVE_OPENCV_VIDEO
    if (cap_) {
        cv::VideoCapture* cap = reinterpret_cast<cv::VideoCapture*>(cap_);
        cv::Mat frame;
        if (!cap->read(frame)) {
            cap->set(cv::CAP_PROP_POS_FRAMES, 0);  // 循环播放
            cap->read(frame);
        }
        if (!frame.empty()) {
            cv::Mat resized;
            cv::resize(frame, resized, cv::Size(SIM_W, SIM_H));
            cv::cvtColor(resized, resized, cv::COLOR_BGR2YUV_I420);
            std::memcpy(buf, resized.data, SIM_FRAME_SIZE);
            return;
        }
    }
#endif
    fill_nv12_pattern(buf, frame_id);
}

bool SimFrameSource::next_frame(uint8_t* buf, uint64_t& ts_us,
                                uint32_t& frame_id, int timeout_ms) {
    (void)timeout_ms;
    // 模拟 30fps：每帧 ~33ms
    static thread_local uint64_t next_tick = now_us();
    uint64_t now = now_us();
    if (now < next_tick) {
        uint64_t sleep_us = next_tick - now;
        std::this_thread::sleep_for(std::chrono::microseconds(sleep_us));
    }
    next_tick += 33333;  // 30 fps

    frame_id = next_fid_++;
    ts_us    = now_us();
    generate_frame(buf, frame_id);
    return true;
}

// ─────────────────────────────────────────────────────────
// SimFrameManager
// ─────────────────────────────────────────────────────────
SimFrameManager::SimFrameManager(int num_channels, const std::string& video_path)
    : num_channels_(num_channels) {

    // 分配内存池（对齐到64字节，便于 SIMD 优化）
    const size_t pool_size = num_channels * 3 * FRAME_SIZE;
    mem_pool_ = static_cast<uint8_t*>(
        ::operator new(pool_size, std::align_val_t{64}));
    std::memset(mem_pool_, 0x10, pool_size);  // Y=16（黑色 NV12）

    channels_ = std::make_unique<ChannelState[]>(num_channels);
    for (int ch = 0; ch < num_channels; ch++) {
        auto& c = channels_[ch];
        for (int b = 0; b < 3; b++) {
            c.bufs[b] = mem_pool_ + (ch * 3 + b) * FRAME_SIZE;
        }
    }

    for (int ch = 0; ch < num_channels; ch++) {
        sources_.push_back(std::make_unique<SimFrameSource>(ch, video_path));
    }
}

SimFrameManager::~SimFrameManager() {
    stop();
    ::operator delete(mem_pool_, std::align_val_t{64});
}

void SimFrameManager::start() {
    running_ = true;
    for (int ch = 0; ch < num_channels_; ch++) {
        cap_threads_.emplace_back([this, ch]() {
            auto& src = sources_[ch];
            auto& cst = channels_[ch];
            while (running_) {
                int wi = cst.write_idx;
                uint64_t ts;
                uint32_t fid;
                if (src->next_frame(cst.bufs[wi], ts, fid)) {
                    std::lock_guard<std::mutex> lk(cst.mtx);
                    cst.ts_us[wi]    = ts;
                    cst.frame_id[wi] = fid;
                    int old_read     = cst.read_idx;
                    cst.read_idx     = wi;
                    cst.write_idx    = (wi + 1) % 3;
                    if (old_read >= 0) cst.drop_count++;
                    cst.cv.notify_one();
                }
            }
        });
    }
}

void SimFrameManager::stop() {
    running_ = false;
    for (int ch = 0; ch < num_channels_; ch++)
        channels_[ch].cv.notify_all();
    for (auto& t : cap_threads_)
        if (t.joinable()) t.join();
    cap_threads_.clear();
}

uint8_t* SimFrameManager::pop_frame(int channel, uint64_t& ts_us,
                                    uint32_t& frame_id, int timeout_ms) {
    if (channel < 0 || channel >= num_channels_) return nullptr;
    auto& cst = channels_[channel];
    std::unique_lock<std::mutex> lk(cst.mtx);
    if (!cst.cv.wait_for(lk, std::chrono::milliseconds(timeout_ms),
                         [&]{ return cst.read_idx >= 0 || !running_; }))
        return nullptr;
    if (cst.read_idx < 0) return nullptr;
    int ri = cst.read_idx;
    cst.read_idx = -1;
    ts_us    = cst.ts_us[ri];
    frame_id = cst.frame_id[ri];
    return cst.bufs[ri];
}

void SimFrameManager::print_stats() const {
    for (int ch = 0; ch < num_channels_; ch++) {
        printf("[SimCapture] CH%d: drop_count=%llu\n",
               ch, (unsigned long long)channels_[ch].drop_count);
    }
}
