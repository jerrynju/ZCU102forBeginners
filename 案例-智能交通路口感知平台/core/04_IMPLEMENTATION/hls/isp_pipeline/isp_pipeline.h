// @req SYS-REQ-001, PERF-REQ-001
// @design DES-ARCH-007
// @test TC-CAM-001
// @author fpga-team | @since 2026-06-04 | @version 1.0
// @status verified
//
// MOD-HLS-ISP: 接口定义
#pragma once
#include "hls_video.h"
#include "ap_axi_sdata.h"
#include "hls_stream.h"
#include <stdint.h>

// ── 分辨率定义 ────────────────────────────────────────────
#define SRC_WIDTH   3840
#define SRC_HEIGHT  2160
#define DST_WIDTH   1920
#define DST_HEIGHT  1080

// ── AXI-Stream 像素类型 ───────────────────────────────────
// 输入：RAW10（Bayer，打包为 16bit）
// 输出：NV12（Y 平面交织，UV 平面交织）
typedef ap_axiu<16, 1, 1, 1> AXI_PIX_IN;   // RAW10 Bayer
typedef ap_axiu<8,  1, 1, 1> AXI_PIX_OUT;  // NV12 byte stream

typedef hls::stream<AXI_PIX_IN>  AXIS_IN;
typedef hls::stream<AXI_PIX_OUT> AXIS_OUT;

// ── Mat 类型 ─────────────────────────────────────────────
typedef hls::Mat<SRC_HEIGHT, SRC_WIDTH, HLS_16UC1> MAT_RAW;
typedef hls::Mat<SRC_HEIGHT, SRC_WIDTH, HLS_8UC3>  MAT_RGB_SRC;
typedef hls::Mat<DST_HEIGHT, DST_WIDTH, HLS_8UC3>  MAT_RGB_DST;
typedef hls::Mat<DST_HEIGHT, DST_WIDTH, HLS_8UC1>  MAT_Y;
typedef hls::Mat<DST_HEIGHT/2, DST_WIDTH/2, HLS_8UC2> MAT_UV;

// ── 控制参数（通过 AXI-Lite 配置）──────────────────────────
struct ISPConfig {
    uint16_t black_level;      // 黑电平（典型值 64，10bit 中）
    uint16_t wb_gain_r;        // 红通道增益（Q8: 1.0 = 256）
    uint16_t wb_gain_g;        // 绿通道增益
    uint16_t wb_gain_b;        // 蓝通道增益
    uint8_t  gamma_lut[256];   // 伽马查找表
    uint8_t  bayer_pattern;    // 0=RGGB, 1=BGGR, 2=GRBG, 3=GBRG
    uint8_t  en_sharpening;    // 锐化使能
    int16_t  ccm[9];           // 色彩校正矩阵（Q8）
};

// ── 顶层函数声明 ──────────────────────────────────────────
void isp_pipeline(
    AXIS_IN&  s_axis_video,   // RAW10 输入流
    AXIS_OUT& m_axis_video,   // NV12 输出流
    uint16_t  black_level,
    uint16_t  wb_gain_r,
    uint16_t  wb_gain_g,
    uint16_t  wb_gain_b,
    uint8_t   bayer_pattern
);

// ── 子模块声明 ────────────────────────────────────────────
void blc_correction(MAT_RAW& src, MAT_RAW& dst, uint16_t level);
void white_balance(MAT_RGB_SRC& src, MAT_RGB_SRC& dst,
                   uint16_t r, uint16_t g, uint16_t b);
void gamma_correct(MAT_RGB_DST& src, MAT_RGB_DST& dst);
void rgb_to_nv12(MAT_RGB_DST& src, AXIS_OUT& dst);
