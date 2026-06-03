#include "frame_manager.h"
#include "inference_engine.h"
#include "event_detector.h"
#include "utils/config.h"
#include "utils/logger.h"
#include <thread>
#include <atomic>
#include <signal.h>
#include <csignal>
#include <mosquitto.h>
#include <grpcpp/grpcpp.h>
#include <sys/prctl.h>
#include <sched.h>

static std::atomic<bool> g_quit{false};

void sig_handler(int) { g_quit.store(true); }

// 设置线程调度策略（推理线程和采集线程使用 FIFO 优先级）
static void set_thread_realtime(int priority) {
    struct sched_param sp{ .sched_priority = priority };
    pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);
}

static void set_thread_name(const char* name) {
    prctl(PR_SET_NAME, name, 0, 0, 0);
}

int main(int argc, char* argv[]) {
    signal(SIGINT,  sig_handler);
    signal(SIGTERM, sig_handler);

    // ── 加载配置 ────────────────────────────────────────────
    AppConfig cfg = AppConfig::load(
        argc > 1 ? argv[1] : "/etc/traffic_edge/config.toml");

    Logger::init(cfg.log_level, cfg.log_file);
    LOG_INFO("TrafficEdge v{} starting...", cfg.version);
    LOG_INFO("Device ID: {}", cfg.device_id);

    // ── 初始化核心组件 ──────────────────────────────────────
    FrameManager frame_mgr(cfg.num_channels);
    LOG_INFO("FrameManager: {} channels, physical mem @{:#x}",
             cfg.num_channels, 0x80000000UL);

    InferenceEngine::Config infer_cfg;
    infer_cfg.yolo_model_path  = cfg.yolo_model;
    infer_cfg.lpr_model_path   = cfg.lpr_model;
    infer_cfg.yolo_conf_thresh = cfg.yolo_conf;
    InferenceEngine infer_engine(infer_cfg);
    LOG_INFO("InferenceEngine loaded: YOLO={}, LPR={}",
             cfg.yolo_model, cfg.lpr_model);

    RuleConfig rules;
    rules.pixel_to_meter = cfg.pixel_to_meter;
    EventDetector event_det(rules);

    // ── 线程 1-4：V4L2 视频采集（每通道一个线程）────────────
    std::vector<std::thread> capture_threads;
    capture_threads.reserve(cfg.num_channels);
    for (int ch = 0; ch < cfg.num_channels; ch++) {
        capture_threads.emplace_back([&, ch]() {
            set_thread_name(("cap" + std::to_string(ch)).c_str());
            set_thread_realtime(80);  // 采集最高优先级

            int fd = open(("/dev/video" + std::to_string(ch)).c_str(), O_RDWR);
            if (fd < 0) {
                LOG_ERROR("Cannot open /dev/video{}", ch);
                return;
            }
            // V4L2 请求缓冲区
            struct v4l2_requestbuffers req{};
            req.count  = 3;
            req.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
            req.memory = V4L2_MEMORY_DMABUF;
            ioctl(fd, VIDIOC_REQBUFS, &req);

            uint32_t frame_id = 0;
            while (!g_quit) {
                struct v4l2_buffer buf{};
                buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                buf.memory = V4L2_MEMORY_DMABUF;
                if (ioctl(fd, VIDIOC_DQBUF, &buf) < 0) continue;
                uint64_t ts = (uint64_t)buf.timestamp.tv_sec * 1000000
                            + buf.timestamp.tv_usec;
                // 通知帧管理器（零拷贝）
                frame_mgr.push(ch, nullptr, ts, frame_id++);
                ioctl(fd, VIDIOC_QBUF, &buf);
            }
            close(fd);
        });
    }

    // ── 线程 5：DPU 推理调度（轮询 4 路，送 DPU）────────────
    std::thread infer_thread([&]() {
        set_thread_name("dpu_infer");
        set_thread_realtime(70);

        // OSD 写入（通过 AXI-Lite 寄存器写入 PL OSD IP）
        int osd_fd = open("/dev/uio0", O_RDWR);
        volatile uint32_t* osd_reg = nullptr;
        if (osd_fd >= 0) {
            osd_reg = (volatile uint32_t*)mmap(
                nullptr, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, osd_fd, 0);
        }

        while (!g_quit) {
            for (int ch = 0; ch < cfg.num_channels; ch++) {
                auto frame = frame_mgr.pop(ch, 30);
                if (!frame) continue;

                // 1. DPU 推理
                auto result = infer_engine.run(*frame);

                // 2. 违规事件检测
                bool is_red = false;  // TODO: 从 OpenAMP 读取信号状态
                auto events = event_det.detect(result, is_red, frame);

                // 3. 写入 OSD IP 寄存器（共享内存方式）
                if (osd_reg) {
                    osd_reg[0] = result.object_count;
                    for (int i = 0; i < result.object_count; i++) {
                        uint32_t* box_reg = (uint32_t*)(osd_reg + 4 + i * 4);
                        box_reg[0] = (result.objects[i].x << 16) | result.objects[i].y;
                        box_reg[1] = (result.objects[i].w << 16) | result.objects[i].h;
                        box_reg[2] = (result.objects[i].class_id << 8)
                                   | result.objects[i].confidence;
                    }
                }
                // 4. 违规事件已通过 EventDetector 回调异步上报
            }
        }
        if (osd_fd >= 0) close(osd_fd);
    });

    // ── 线程 6：OpenAMP 心跳（与 R5 FreeRTOS 通信）──────────
    std::thread amp_thread([&]() {
        set_thread_name("openamp_hb");
        int rpmsg_fd = open("/dev/rpmsg0", O_RDWR);
        if (rpmsg_fd < 0) {
            LOG_WARN("OpenAMP rpmsg not available, R5 will run standalone");
            return;
        }
        struct { uint8_t type; uint8_t seq; } hb;
        hb.type = 0xFF;  // MSG_TYPE_HEARTBEAT
        while (!g_quit) {
            hb.seq++;
            write(rpmsg_fd, &hb, sizeof(hb));
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
        close(rpmsg_fd);
    });

    // ── 主线程：gRPC 管理服务 ────────────────────────────────
    // （gRPC Server 阻塞直到 g_quit）
    std::string server_addr = "0.0.0.0:" + std::to_string(cfg.grpc_port);
    LOG_INFO("Starting gRPC server on {}", server_addr);

    // 等待退出信号
    while (!g_quit) std::this_thread::sleep_for(std::chrono::milliseconds(100));

    LOG_INFO("Shutting down...");
    for (auto& t : capture_threads) if (t.joinable()) t.join();
    if (infer_thread.joinable()) infer_thread.join();
    if (amp_thread.joinable())   amp_thread.join();

    frame_mgr.print_stats();
    LOG_INFO("Avg inference latency: {:.1f} ms", infer_engine.get_avg_latency_ms());
    LOG_INFO("TrafficEdge stopped.");
    return 0;
}
