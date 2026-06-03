#pragma once
#include <string>
#include <cstdint>

struct AppConfig {
    // 基本信息
    std::string version{"2.3.1"};
    std::string device_id{"edge_unknown"};
    std::string log_level{"info"};
    std::string log_file{"/var/log/traffic_edge.log"};

    // 视频采集
    int  num_channels{4};
    int  capture_width{1920};
    int  capture_height{1080};
    int  capture_fps{30};

    // AI 模型
    std::string yolo_model{"/opt/models/yolov8s_traffic.xmodel"};
    std::string lpr_model {"/opt/models/lprnet.xmodel"};
    float       yolo_conf {0.40f};
    float       yolo_nms  {0.50f};

    // 事件检测参数
    float pixel_to_meter{0.05f};  // 需要现场标定

    // 云端通信
    std::string mqtt_broker{"mqtt.traffic.example.com"};
    int         mqtt_port{8883};
    std::string mqtt_user{};
    std::string mqtt_password{};
    std::string mqtt_ca_cert{"/etc/ssl/certs/traffic_ca.crt"};
    std::string device_cert{"/etc/ssl/device/device.crt"};
    std::string device_key {"/etc/ssl/device/device.key"};

    // gRPC 管理接口
    int  grpc_port{50051};
    bool grpc_tls_enable{true};

    // REST/WebSocket 本地服务
    int  rest_port{8080};

    // OTA
    std::string ota_check_url{"https://ota.traffic.example.com/check"};
    int         ota_check_interval_h{24};

    static AppConfig load(const std::string& path);
    void save(const std::string& path) const;
};
