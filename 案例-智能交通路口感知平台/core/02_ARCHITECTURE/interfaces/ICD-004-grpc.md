---
id: ICD-004
title: gRPC 管理接口
type: interface-control
status: approved
owner: backend-team
version: 1.0
traces: { up: [STK-REQ-004, DES-ARCH-004], down: [MOD-C-GRPC] }
tags: [interface, grpc, management]
---

# ICD-004: gRPC 管理接口

## Proto 定义

文件：`core/04_IMPLEMENTATION/proto/traffic_edge.proto`

```protobuf
syntax = "proto3";
import "google/protobuf/timestamp.proto";

package trafficedge.v1;

service TrafficEdgeManagement {
    rpc GetDeviceStatus(GetStatusRequest) returns (DeviceStatus);
    rpc StreamDetections(StreamRequest) returns (stream DetectionEvent);
    rpc QueryHistory(HistoryRequest) returns (HistoryResponse);
    rpc UpdateConfig(UpdateConfigRequest) returns (UpdateConfigResponse);
    rpc ControlSignal(SignalControlRequest) returns (SignalControlResponse);
    rpc TriggerCapture(CaptureRequest) returns (CaptureResponse);
}

message DeviceStatus {
    string  device_id    = 1;
    google.protobuf.Timestamp ts = 2;
    string  version      = 3;
    string  hw_version   = 4;
    bool    online       = 5;
    SystemMetrics metrics = 6;
    repeated ChannelStatus channels = 7;
}

message SystemMetrics {
    float cpu_usage_pct    = 1;
    float mem_usage_pct    = 2;
    float temp_celsius     = 3;
    float dpu_usage_pct    = 4;
    uint64 uptime_seconds  = 5;
    string primary_link    = 6;
    uint32 link_speed_mbps = 7;
}

message DetectionEvent {
    google.protobuf.Timestamp ts = 1;
    uint32 channel    = 2;
    uint32 frame_id   = 3;
    repeated DetectedObject objects = 4;
    bytes  preview_jpeg = 5;
}

message DetectedObject {
    uint32 track_id   = 1;
    uint32 class_id   = 2;
    float  confidence = 3;
    BoundingBox bbox  = 4;
    string plate      = 5;
    float  speed_kmh  = 6;
}
```

## 端口

- gRPC: 50051（TLS）
- HTTP/REST: 8080
- WebSocket: 8081
