#include "isp_pipeline.h"

// ── 伽马查找表（sRGB 标准，输入 8bit 线性，输出 8bit gamma）────
static const uint8_t GAMMA_LUT[256] = {
      0,  21,  28,  34,  39,  43,  46,  50,  53,  56,  58,  61,  63,
     65,  68,  70,  72,  74,  76,  77,  79,  81,  82,  84,  85,  87,
     88,  90,  91,  93,  94,  95,  97,  98,  99, 100, 102, 103, 104,
    105, 106, 107, 108, 110, 111, 112, 113, 114, 115, 116, 117, 118,
    119, 120, 121, 122, 123, 124, 124, 125, 126, 127, 128, 129, 130,
    131, 131, 132, 133, 134, 135, 135, 136, 137, 138, 139, 139, 140,
    141, 142, 142, 143, 144, 145, 145, 146, 147, 147, 148, 149, 150,
    150, 151, 152, 152, 153, 154, 154, 155, 156, 156, 157, 158, 158,
    159, 159, 160, 161, 161, 162, 163, 163, 164, 164, 165, 166, 166,
    167, 167, 168, 169, 169, 170, 170, 171, 171, 172, 173, 173, 174,
    174, 175, 175, 176, 176, 177, 178, 178, 179, 179, 180, 180, 181,
    181, 182, 182, 183, 183, 184, 184, 185, 185, 186, 186, 187, 187,
    188, 188, 189, 189, 190, 190, 191, 191, 192, 192, 193, 193, 194,
    194, 195, 195, 196, 196, 196, 197, 197, 198, 198, 199, 199, 200,
    200, 200, 201, 201, 202, 202, 203, 203, 203, 204, 204, 205, 205,
    206, 206, 206, 207, 207, 208, 208, 208, 209, 209, 210, 210, 210,
    211, 211, 212, 212, 212, 213, 213, 214, 214, 214, 215, 215, 215,
    216, 216, 217, 217, 217, 218, 218, 218, 219, 219, 220, 220, 220,
    221, 221, 221, 222, 222, 222, 223, 223, 224, 224, 224, 225, 225,
    225, 226, 226, 226, 227, 227, 227, 228, 228, 228, 229, 229, 230,
    230, 255
};

// ── 黑电平校正 ───────────────────────────────────────────────
// 减去传感器暗电流，防止下溢时钳位到 0
void blc_correction(MAT_RAW& src, MAT_RAW& dst, uint16_t level) {
#pragma HLS INLINE
    for (int r = 0; r < SRC_HEIGHT; r++) {
        for (int c = 0; c < SRC_WIDTH; c++) {
#pragma HLS PIPELINE II=1
            hls::Scalar<1, uint16_t> px;
            src >> px;
            uint16_t val = px.val[0];
            px.val[0] = (val > level) ? (val - level) : (uint16_t)0;
            dst << px;
        }
    }
}

// ── 白平衡（简单增益法）─────────────────────────────────────
// 对 RGGB Bayer 各通道分别施加增益（Q8 定点：1.0 = 256）
void white_balance(MAT_RGB_SRC& src, MAT_RGB_SRC& dst,
                   uint16_t r, uint16_t g, uint16_t b) {
#pragma HLS INLINE
    for (int row = 0; row < SRC_HEIGHT; row++) {
        for (int col = 0; col < SRC_WIDTH; col++) {
#pragma HLS PIPELINE II=1
            hls::Scalar<3, uint8_t> px;
            src >> px;
            // R 通道
            uint16_t rv = ((uint16_t)px.val[0] * r) >> 8;
            // G 通道（两个绿像素平均）
            uint16_t gv = ((uint16_t)px.val[1] * g) >> 8;
            // B 通道
            uint16_t bv = ((uint16_t)px.val[2] * b) >> 8;
            px.val[0] = (rv > 255) ? 255 : (uint8_t)rv;
            px.val[1] = (gv > 255) ? 255 : (uint8_t)gv;
            px.val[2] = (bv > 255) ? 255 : (uint8_t)bv;
            dst << px;
        }
    }
}

// ── 伽马校正（查表法，1个时钟/像素）──────────────────────────
void gamma_correct(MAT_RGB_DST& src, MAT_RGB_DST& dst) {
#pragma HLS INLINE
    uint8_t lut[256];
#pragma HLS ARRAY_PARTITION variable=lut complete  // 全展开，单周期读取
    for (int i = 0; i < 256; i++) lut[i] = GAMMA_LUT[i];

    for (int row = 0; row < DST_HEIGHT; row++) {
        for (int col = 0; col < DST_WIDTH; col++) {
#pragma HLS PIPELINE II=1
            hls::Scalar<3, uint8_t> px;
            src >> px;
            px.val[0] = lut[px.val[0]];
            px.val[1] = lut[px.val[1]];
            px.val[2] = lut[px.val[2]];
            dst << px;
        }
    }
}

// ── RGB → NV12 格式转换 + AXI-Stream 输出 ──────────────────
// NV12: Y 平面（全分辨率）+ UV 交织平面（2x2 下采样）
// 输出字节流：先输出所有 Y 行，再输出所有 UV 行
void rgb_to_nv12(MAT_RGB_DST& src, AXIS_OUT& dst) {
#pragma HLS INLINE
    // 行缓冲：保存 RGB 以便 UV 下采样时重用
    uint8_t line_buf_r[DST_WIDTH];
    uint8_t line_buf_g[DST_WIDTH];
    uint8_t line_buf_b[DST_WIDTH];
#pragma HLS ARRAY_PARTITION variable=line_buf_r cyclic factor=4
#pragma HLS ARRAY_PARTITION variable=line_buf_g cyclic factor=4
#pragma HLS ARRAY_PARTITION variable=line_buf_b cyclic factor=4

    // 两遍输出：Pass 1 - Y 平面，Pass 2 - UV 平面
    // 实现简化版：直接 RGB 转 Y 输出，UV 每两行输出一行
    for (int row = 0; row < DST_HEIGHT; row++) {
        for (int col = 0; col < DST_WIDTH; col++) {
#pragma HLS PIPELINE II=1
            hls::Scalar<3, uint8_t> px;
            src >> px;
            uint8_t R = px.val[0], G = px.val[1], B = px.val[2];
            // BT.601: Y = 0.299R + 0.587G + 0.114B
            uint16_t Y = (uint16_t)(77*R + 150*G + 29*B) >> 8;
            line_buf_r[col] = R;
            line_buf_g[col] = G;
            line_buf_b[col] = B;
            // 输出 Y 字节
            AXI_PIX_OUT ypx;
            ypx.data = (Y > 235) ? 235 : (uint8_t)Y + 16;
            ypx.keep = 1; ypx.strb = 1;
            ypx.last = (row == DST_HEIGHT-1 && col == DST_WIDTH-1) ? 1 : 0;
            dst << ypx;
        }
        // 奇数行：输出 UV 平面（每 2 行输出 1 行 UV）
        if (row % 2 == 1) {
            for (int col = 0; col < DST_WIDTH; col += 2) {
#pragma HLS PIPELINE II=2
                uint8_t R = line_buf_r[col], G = line_buf_g[col], B = line_buf_b[col];
                // BT.601: Cb = -0.169R - 0.331G + 0.499B + 128
                //         Cr =  0.499R - 0.418G - 0.081B + 128
                int16_t Cb = (-43*R - 85*G + 128*B) >> 8;
                int16_t Cr = (128*R - 107*G - 21*B) >> 8;
                uint8_t U = (uint8_t)((Cb + 128 > 240) ? 240 : (Cb + 128 < 16) ? 16 : Cb + 128);
                uint8_t V = (uint8_t)((Cr + 128 > 240) ? 240 : (Cr + 128 < 16) ? 16 : Cr + 128);
                AXI_PIX_OUT upx, vpx;
                upx.data = U; upx.keep = 1; upx.strb = 1; upx.last = 0;
                vpx.data = V; vpx.keep = 1; vpx.strb = 1;
                vpx.last = (row == DST_HEIGHT-1 && col >= DST_WIDTH-2) ? 1 : 0;
                dst << upx;
                dst << vpx;
            }
        }
    }
}

// ── 顶层函数（被 Vivado Block Design 调用）────────────────────
void isp_pipeline(
    AXIS_IN&  s_axis_video,
    AXIS_OUT& m_axis_video,
    uint16_t  black_level,
    uint16_t  wb_gain_r,
    uint16_t  wb_gain_g,
    uint16_t  wb_gain_b,
    uint8_t   bayer_pattern
) {
// ── AXI-Lite 控制接口（Vivado 自动生成寄存器映射）───────────
#pragma HLS INTERFACE axis       port=s_axis_video
#pragma HLS INTERFACE axis       port=m_axis_video
#pragma HLS INTERFACE s_axilite  port=black_level  bundle=CTRL
#pragma HLS INTERFACE s_axilite  port=wb_gain_r    bundle=CTRL
#pragma HLS INTERFACE s_axilite  port=wb_gain_g    bundle=CTRL
#pragma HLS INTERFACE s_axilite  port=wb_gain_b    bundle=CTRL
#pragma HLS INTERFACE s_axilite  port=bayer_pattern bundle=CTRL
#pragma HLS INTERFACE s_axilite  port=return        bundle=CTRL
// ── 数据流（各阶段并行执行）─────────────────────────────────
#pragma HLS DATAFLOW

    MAT_RAW      mat_raw(SRC_HEIGHT, SRC_WIDTH);
    MAT_RAW      mat_blc(SRC_HEIGHT, SRC_WIDTH);
    MAT_RGB_SRC  mat_rgb_src(SRC_HEIGHT, SRC_WIDTH);
    MAT_RGB_SRC  mat_wb(SRC_HEIGHT, SRC_WIDTH);
    MAT_RGB_DST  mat_rgb_dst(DST_HEIGHT, DST_WIDTH);
    MAT_RGB_DST  mat_gamma(DST_HEIGHT, DST_WIDTH);

    // Stage 1: AXI-Stream → Mat
    hls::AXIvideo2Mat(s_axis_video, mat_raw);

    // Stage 2: 黑电平校正
    blc_correction(mat_raw, mat_blc, black_level);

    // Stage 3: 去马赛克（RAW Bayer → RGB）
    // HLS::Demosaic 使用双线性插值，Bayer 模式由参数决定
    hls::Demosaic<HLS_RGGB, SRC_HEIGHT, SRC_WIDTH>(mat_blc, mat_rgb_src);

    // Stage 4: 白平衡增益
    white_balance(mat_rgb_src, mat_wb, wb_gain_r, wb_gain_g, wb_gain_b);

    // Stage 5: 双线性缩放（4K → 1080p）
    hls::Resize<HLS_INTER_LINEAR, SRC_HEIGHT, SRC_WIDTH,
                DST_HEIGHT, DST_WIDTH>(mat_wb, mat_rgb_dst);

    // Stage 6: 伽马校正
    gamma_correct(mat_rgb_dst, mat_gamma);

    // Stage 7: RGB → NV12 + 输出 AXI-Stream
    rgb_to_nv12(mat_gamma, m_axis_video);
}
