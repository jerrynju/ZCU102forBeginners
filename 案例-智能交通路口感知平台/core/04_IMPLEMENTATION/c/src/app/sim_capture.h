#pragma once
/**
 * 仿真帧源（SimCapture）
 * 在无 FPGA/V4L2 硬件时，用软件生成 NV12 视频帧替代摄像头输入
 * 通过 --sim 或 --sim-video 编译/运行时参数激活
 *
 * 生成内容：
 *   - 移动灰度渐变色块（模拟多目标）
 *   - 时间戳叠加（验证帧序列连续性）
 *   - 可选：从视频文件读取（需提供 --sim-video 路径）
 */

#include <cstdint>
#include <string>
#include <atomic>
#include <memory>
#include <functional>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>

// NV12 单帧大小（与 FrameManager 保持一致）
static constexpr int SIM_W = 1920;
static constexpr int SIM_H = 1080;
static constexpr size_t SIM_FRAME_SIZE = SIM_W * SIM_H * 3 / 2;  // NV12

/**
 * 合成 NV12 帧生成器
 * 生成带有移动方块的测试图案，用于端到端管道验证
 */
class SimFrameSource {
public:
    explicit SimFrameSource(int channel, const std::string& video_path = "");
    ~SimFrameSource();

    /**
     * 阻塞等待下一帧（超时返回 false）
     * @param buf      目标 NV12 缓冲区（调用方分配 SIM_FRAME_SIZE 字节）
     * @param ts_us    输出时间戳（微秒）
     * @param frame_id 输出帧序号
     * @param timeout_ms 超时毫秒数
     */
    bool next_frame(uint8_t* buf, uint64_t& ts_us, uint32_t& frame_id,
                    int timeout_ms = 100);

    // 生成单帧到指定缓冲区（不阻塞，立即返回）
    void generate_frame(uint8_t* buf, uint32_t frame_id) const;

    bool is_open() const { return open_; }

private:
    int         channel_;
    std::string video_path_;
    bool        open_{false};
    uint32_t    next_fid_{0};
    std::atomic<bool> running_{false};

    // 视频文件模式（使用 OpenCV VideoCapture）
    void* cap_{nullptr};  // cv::VideoCapture*

    void fill_nv12_pattern(uint8_t* buf, uint32_t frame_id) const;
};

/**
 * 仿真 FrameManager 替代品
 * 当以 --sim 运行时，替换 /dev/mem mmap，使用堆内存作为帧缓冲
 */
class SimFrameManager {
public:
    static constexpr int MAX_CHANNELS = 4;
    static constexpr size_t FRAME_SIZE = SIM_FRAME_SIZE;

    explicit SimFrameManager(int num_channels, const std::string& video_path = "");
    ~SimFrameManager();

    // 启动后台采集线程（模拟 V4L2 DMABUF 采集）
    void start();
    void stop();

    // 取最新帧（阻塞，超时返回 nullptr）
    // 返回的 uint8_t* 指向内部缓冲区，有效期到下次调用
    uint8_t* pop_frame(int channel, uint64_t& ts_us, uint32_t& frame_id,
                       int timeout_ms = 50);

    void print_stats() const;

private:
    int    num_channels_;
    bool   running_{false};

    // 每通道三重缓冲
    struct ChannelState {
        uint8_t*        bufs[3];
        int             write_idx{0};
        int             read_idx{-1};
        uint64_t        ts_us[3]{};
        uint32_t        frame_id[3]{};
        uint64_t        drop_count{0};
        std::mutex      mtx;
        std::condition_variable cv;
    };

    std::unique_ptr<ChannelState[]>     channels_;
    std::vector<std::thread>            cap_threads_;
    std::vector<std::unique_ptr<SimFrameSource>> sources_;
    uint8_t* mem_pool_{nullptr};  // 统一内存池 num_ch × 3 × FRAME_SIZE
};
