// @req SYS-REQ-001, IF-REQ-005
// @design DES-ARCH-007, ICD-006
// @test TC-IF-DP-002
// @author fpga-team | @since 2026-06-04 | @version 1.0
// @status verified
//
// MOD-HLS-OSD: 接口定义
#pragma once
#include "ap_axi_sdata.h"
#include "hls_stream.h"
#include <stdint.h>

#define FRAME_WIDTH  1920
#define FRAME_HEIGHT 1080
#define MAX_BOXES    64
#define BOX_THICKNESS 3
#define MAX_LABEL_LEN 16

typedef ap_axiu<24, 1, 1, 1> AXI_PIX;  // RGB888
typedef hls::stream<AXI_PIX> AXIS_VIDEO;

// 检测框描述符（与 PS 共享内存对齐）
struct OSDBox {
    uint16_t x, y, w, h;      // 像素坐标
    uint8_t  class_id;         // 类别（决定颜色）
    uint8_t  confidence;       // 置信度 0-100
    uint8_t  track_id;         // 跟踪 ID（用于显示）
    uint8_t  flags;            // bit0: 有车牌, bit1: 违规
};

// 类别颜色表（BGR888）
static const uint32_t CLASS_COLORS[8] = {
    0xFF4444,  // car:        红
    0x44FF44,  // truck:      绿
    0x4444FF,  // bus:        蓝
    0xFFFF44,  // person:     黄
    0xFF44FF,  // motorcycle: 紫
    0x44FFFF,  // bicycle:    青
    0xFF8800,  // plate:      橙
    0xFFFFFF,  // 默认:       白
};

void osd_overlay(
    AXIS_VIDEO& s_video,
    AXIS_VIDEO& m_video,
    OSDBox*     boxes,
    uint8_t     box_count,
    uint32_t    timestamp_s,   // 叠加时间戳
    uint8_t     channel_id     // 通道号显示
);
