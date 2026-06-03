#include "frame_manager.h"
#include "inference_engine.h"
#include "event_detector.h"
#include "sim_capture.h"
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
#include <cstring>

static std::atomic<bool> g_quit{false};

void sig_handler(int) { g_quit.store(true); }

static void set_thread_realtime(int priority) {
    struct sched_param sp{ .sched_priority = priority };
    pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);
}

static void set_thread_name(const char* name) {
    prctl(PR_SET_NAME, name, 0, 0, 0);
}

// 解析 --sim / --sim-video <path> 参数
static bool parse_sim_flags(int argc, char* argv[],
                             bool& sim_mode, std::string& sim_video,
                             std::string& config_path) {
    sim_mode    = false;
    sim_video   = "";
    config_path = "/etc/traffic_edge/config.toml";
    for (int i = 1; i < argc; i++) {
        if (std::strcmp(argv[i], "--sim") == 0) {
            sim_mode = true;
        } else if (std::strcmp(argv[i], "--sim-video") == 0 && i + 1 < argc) {
            sim_mode  = true;
            sim_video = argv[++i];
        } else if (argv[i][0] != '-') {
            config_path = argv[i];
        }
    }
    return true;
}

int main(int argc, char* argv[]) {
    signal(SIGINT,  sig_handler);
    signal(SIGTERM, sig_handler);

    // ── 解析命令行（仿真标志）──────────────────────────────
    bool        sim_mode   = false;
    std::string sim_video  = "";
    std::string cfg_path;
    parse_sim_flags(argc, argv, sim_mode, sim_video, cfg_path);

    // ── 加载配置 ────────────────────────────────────────────
    AppConfig cfg = AppConfig::load(cfg_path);

    Logger::init(cfg.log_level, cfg.log_file);
    LOG_INFO("TrafficEdge v{} starting... [{}]",
             cfg.version, sim_mode ? "SIMULATION MODE" : "HARDWARE MODE");
    LOG_INFO("Device ID: {}", cfg.device_id);
    if (sim_mode)
        LOG_WARN("** 仿真模式：无需 FPGA/摄像头/DPU 硬件 **");

    // ── 初始化推理和事件检测（硬件/仿真共用）──────────────
    InferenceEngine::Config infer_cfg;
    infer_cfg.yolo_model_path  = cfg.yolo_model;
    infer_cfg.lpr_model_path   = cfg.lpr_model;
    infer_cfg.yolo_conf_thresh = cfg.yolo_conf;
    infer_cfg.sim_mode         = sim_mode;  // 仿真模式下用 MockDetector
    InferenceEngine infer_engine(infer_cfg);

    RuleConfig rules;
    rules.pixel_to_meter = cfg.pixel_to_meter;
    EventDetector event_det(rules);

    // ── 仿真帧管理器（仿真模式）OR 真实 FrameManager ────────
    std::unique_ptr<SimFrameManager> sim_frame_mgr;
    std::unique_ptr<FrameManager>    hw_frame_mgr;

    if (sim_mode) {
        sim_frame_mgr = std::make_unique<SimFrameManager>(cfg.num_channels, sim_video);
        sim_frame_mgr->start();
        LOG_INFO("SimFrameManager 启动: {} 通道, 视频源={}",
                 cfg.num_channels, sim_video.empty() ? "合成图案" : sim_video);
    } else {
        hw_frame_mgr = std::make_unique<FrameManager>(cfg.num_channels);
        LOG_INFO("FrameManager: {} 通道, 物理内存 @{:#x}",
                 cfg.num_channels, 0x80000000UL);
    }

    // ── 线程 1-4：视频采集 ──────────────────────────────────
    std::vector<std::thread> capture_threads;
    capture_threads.reserve(cfg.num_channels);

    if (!sim_mode) {
        // 真实 V4L2 采集（原始代码）
        for (int ch = 0; ch < cfg.num_channels; ch++) {
            capture_threads.emplace_back([&, ch]() {
                set_thread_name(("cap" + std::to_string(ch)).c_str());
                set_thread_realtime(80);

                int fd = open(("/dev/video" + std::to_string(ch)).c_str(), O_RDWR);
                if (fd < 0) { LOG_ERROR("Cannot open /dev/video{}", ch); return; }

                struct v4l2_requestbuffers req{};
                req.count  = 3;
                req.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                req.memory = V4L2_MEMORY_DMABUF;
                ioctl(fd, VIDIOC_REQBUFS, &req);

                uint32_t fid = 0;
                while (!g_quit) {
                    struct v4l2_buffer buf{};
                    buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                    buf.memory = V4L2_MEMORY_DMABUF;
                    if (ioctl(fd, VIDIOC_DQBUF, &buf) < 0) continue;
                    uint64_t ts = (uint64_t)buf.timestamp.tv_sec * 1000000
                                + buf.timestamp.tv_usec;
                    hw_frame_mgr->push(ch, nullptr, ts, fid++);
                    ioctl(fd, VIDIOC_QBUF, &buf);
                }
                close(fd);
            });
        }
    }
    // 仿真模式：SimFrameManager 内部已有采集线程，无需额外线程

    // ── 线程 5：推理调度 ────────────────────────────────────
    std::thread infer_thread([&]() {
        set_thread_name(sim_mode ? "sim_infer" : "dpu_infer");
        if (!sim_mode) set_thread_realtime(70);

        // OSD 写入（仿真模式跳过）
        int osd_fd = -1;
        volatile uint32_t* osd_reg = nullptr;
        if (!sim_mode) {
            osd_fd = open("/dev/uio0", O_RDWR);
            if (osd_fd >= 0) {
                osd_reg = (volatile uint32_t*)mmap(
                    nullptr, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, osd_fd, 0);
            }
        }

        uint64_t frame_count = 0;
        while (!g_quit) {
            for (int ch = 0; ch < cfg.num_channels; ch++) {
                // 获取帧（根据模式从不同来源）
                std::shared_ptr<VideoFrame> hw_frame;
                uint8_t* sim_buf = nullptr;
                uint64_t ts_us; uint32_t fid;

                if (sim_mode) {
                    sim_buf = sim_frame_mgr->pop_frame(ch, ts_us, fid, 30);
                    if (!sim_buf) continue;
                    // 构造虚拟 VideoFrame 指向仿真缓冲
                    VideoFrame vf;
                    vf.channel    = ch;
                    vf.frame_id   = fid;
                    vf.timestamp_us = ts_us;
                    vf.data_nv12  = sim_buf;
                    vf.size       = SimFrameManager::FRAME_SIZE;
                    vf.width      = 1920; vf.height = 1080;
                    auto result   = infer_engine.run(vf);
                    bool is_red   = false;
                    auto events   = event_det.detect(result, is_red, nullptr);
                    frame_count++;
                    if (frame_count % 300 == 0)
                        LOG_INFO("[SIM] ch={} 已处理 {} 帧，检测 {} 目标",
                                 ch, frame_count, result.object_count);
                } else {
                    hw_frame = hw_frame_mgr->pop(ch, 30);
                    if (!hw_frame) continue;
                    auto result = infer_engine.run(*hw_frame);
                    bool is_red = false;
                    auto events = event_det.detect(result, is_red, hw_frame);
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
                }
            }
        }
        if (osd_fd >= 0) close(osd_fd);
    });

    // ── 线程 6：OpenAMP / 仿真心跳 ──────────────────────────
    std::thread amp_thread([&]() {
        set_thread_name(sim_mode ? "sim_hb" : "openamp_hb");
        if (sim_mode) {
            // 仿真模式：每秒打印一行状态日志
            int tick = 0;
            while (!g_quit) {
                std::this_thread::sleep_for(std::chrono::seconds(1));
                LOG_DEBUG("[SIM] heartbeat tick={}", ++tick);
            }
            return;
        }
        int rpmsg_fd = open("/dev/rpmsg0", O_RDWR);
        if (rpmsg_fd < 0) {
            LOG_WARN("OpenAMP rpmsg 不可用，R5 将独立运行");
            return;
        }
        struct { uint8_t type; uint8_t seq; } hb;
        hb.type = 0xFF;
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

    // ── 主线程：gRPC 管理服务 ────────────────────────────────
    std::string server_addr = "0.0.0.0:" + std::to_string(cfg.grpc_port);
    LOG_INFO("gRPC server: {}", server_addr);

    // 等待退出信号
    while (!g_quit) std::this_thread::sleep_for(std::chrono::milliseconds(100));

    LOG_INFO("Shutting down...");
    if (sim_mode) {
        sim_frame_mgr->stop();
        sim_frame_mgr->print_stats();
    }
    for (auto& t : capture_threads) if (t.joinable()) t.join();
    if (infer_thread.joinable()) infer_thread.join();
    if (amp_thread.joinable())   amp_thread.join();
    if (!sim_mode && hw_frame_mgr) hw_frame_mgr->print_stats();
    LOG_INFO("Avg inference latency: {:.1f} ms", infer_engine.get_avg_latency_ms());
    LOG_INFO("TrafficEdge stopped.");
    return 0;
}
