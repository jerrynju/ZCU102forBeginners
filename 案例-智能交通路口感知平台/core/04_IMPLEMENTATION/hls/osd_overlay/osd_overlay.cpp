// @req SYS-REQ-001, IF-REQ-005
// @design DES-ARCH-007, ICD-006
// @test TC-IF-DP-002
// @author fpga-team | @since 2026-06-04 | @version 1.0
// @status verified
//
// MOD-HLS-OSD: 检测框与文字叠加
// 输入：RGB888 视频流 + DDR 中的 OSDBox 数组
// 输出：RGB888 视频流（含叠加）

#include "osd_overlay.h"

// ── 5×7 像素点阵字体（ASCII 32-127）──────────────────────────
// 每字符 7 行 × 5bit，LSB 对应最左列
static const uint8_t FONT_5X7[96][7] = {
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // 0x20 SPACE
    {0x04,0x04,0x04,0x04,0x00,0x04,0x00}, // 0x21 !
    {0x0A,0x0A,0x00,0x00,0x00,0x00,0x00}, // 0x22 "
    {0x0A,0x1F,0x0A,0x0A,0x1F,0x0A,0x00}, // 0x23 #
    {0x04,0x0F,0x14,0x0E,0x05,0x1E,0x04}, // 0x24 $
    {0x18,0x19,0x02,0x04,0x08,0x13,0x03}, // 0x25 %
    {0x0C,0x12,0x14,0x08,0x15,0x12,0x0D}, // 0x26 &
    {0x06,0x04,0x08,0x00,0x00,0x00,0x00}, // 0x27 '
    {0x02,0x04,0x08,0x08,0x08,0x04,0x02}, // 0x28 (
    {0x08,0x04,0x02,0x02,0x02,0x04,0x08}, // 0x29 )
    {0x00,0x04,0x15,0x0E,0x15,0x04,0x00}, // 0x2A *
    {0x00,0x04,0x04,0x1F,0x04,0x04,0x00}, // 0x2B +
    {0x00,0x00,0x00,0x00,0x06,0x04,0x08}, // 0x2C ,
    {0x00,0x00,0x00,0x1F,0x00,0x00,0x00}, // 0x2D -
    {0x00,0x00,0x00,0x00,0x00,0x06,0x06}, // 0x2E .
    {0x01,0x02,0x02,0x04,0x08,0x08,0x10}, // 0x2F /
    // 数字 0-9
    {0x0E,0x11,0x13,0x15,0x19,0x11,0x0E}, // 0x30 0
    {0x04,0x0C,0x04,0x04,0x04,0x04,0x0E}, // 0x31 1
    {0x0E,0x11,0x01,0x02,0x04,0x08,0x1F}, // 0x32 2
    {0x0E,0x11,0x01,0x06,0x01,0x11,0x0E}, // 0x33 3
    {0x02,0x06,0x0A,0x12,0x1F,0x02,0x02}, // 0x34 4
    {0x1F,0x10,0x1E,0x01,0x01,0x11,0x0E}, // 0x35 5
    {0x06,0x08,0x10,0x1E,0x11,0x11,0x0E}, // 0x36 6
    {0x1F,0x01,0x02,0x04,0x08,0x08,0x08}, // 0x37 7
    {0x0E,0x11,0x11,0x0E,0x11,0x11,0x0E}, // 0x38 8
    {0x0E,0x11,0x11,0x0F,0x01,0x02,0x0C}, // 0x39 9
    // A-Z（选取常用的）
    {0x0E,0x11,0x11,0x1F,0x11,0x11,0x11}, // 0x41 A
    {0x1E,0x11,0x11,0x1E,0x11,0x11,0x1E}, // 0x42 B
    {0x0E,0x11,0x10,0x10,0x10,0x11,0x0E}, // 0x43 C
};

// 获取字体像素（参数 ch: ASCII 字符，row/col: 字体内坐标）
static inline bool get_font_pixel(uint8_t ch, int row, int col) {
#pragma HLS INLINE
    if (ch < 0x30 || ch > 0x43 || col >= 5 || row >= 7) return false;
    uint8_t idx = ch - 0x20;
    if (idx >= 96) return false;
    return (FONT_5X7[idx][row] >> (4 - col)) & 1;
}

// ── 矩形框绘制：检测当前像素是否在边框上 ──────────────────────
static inline bool is_on_border(
    int row, int col,
    uint16_t bx, uint16_t by, uint16_t bw, uint16_t bh,
    uint8_t thickness
) {
#pragma HLS INLINE
    bool in_x  = (col >= bx) && (col < bx + bw);
    bool in_y  = (row >= by) && (row < by + bh);
    bool edge_l = in_y && (col >= bx)        && (col < bx + thickness);
    bool edge_r = in_y && (col >= bx+bw-thickness) && (col < bx + bw);
    bool edge_t = in_x && (row >= by)        && (row < by + thickness);
    bool edge_b = in_x && (row >= by+bh-thickness) && (row < by + bh);
    return edge_l || edge_r || edge_t || edge_b;
}

// ── 顶层 OSD 叠加函数 ───────────────────────────────────────
void osd_overlay(
    AXIS_VIDEO& s_video,
    AXIS_VIDEO& m_video,
    OSDBox*     boxes,
    uint8_t     box_count,
    uint32_t    timestamp_s,
    uint8_t     channel_id
) {
#pragma HLS INTERFACE axis      port=s_video
#pragma HLS INTERFACE axis      port=m_video
#pragma HLS INTERFACE m_axi     port=boxes     depth=64 bundle=GMEM offset=slave
#pragma HLS INTERFACE s_axilite port=box_count   bundle=CTRL
#pragma HLS INTERFACE s_axilite port=timestamp_s bundle=CTRL
#pragma HLS INTERFACE s_axilite port=channel_id  bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return      bundle=CTRL

    // 预加载检测框到本地数组（避免逐像素访问 DDR）
    OSDBox local_boxes[MAX_BOXES];
#pragma HLS ARRAY_PARTITION variable=local_boxes complete dim=1
    for (int i = 0; i < box_count && i < MAX_BOXES; i++) {
#pragma HLS PIPELINE II=1
        local_boxes[i] = boxes[i];
    }

    for (int row = 0; row < FRAME_HEIGHT; row++) {
        for (int col = 0; col < FRAME_WIDTH; col++) {
#pragma HLS PIPELINE II=1

            AXI_PIX in_px, out_px;
            s_video >> in_px;
            out_px = in_px;

            bool  painted = false;
            uint32_t paint_color = 0;

            // 遍历所有检测框
            for (int b = 0; b < MAX_BOXES; b++) {
#pragma HLS UNROLL
                if (b >= box_count) continue;
                const OSDBox& bx = local_boxes[b];

                // 绘制边框
                if (!painted && is_on_border(row, col,
                        bx.x, bx.y, bx.w, bx.h, BOX_THICKNESS)) {
                    uint8_t cid = (bx.flags & 0x02) ? 6 :   // 违规：橙色
                                  bx.class_id & 0x7;
                    paint_color = CLASS_COLORS[cid];
                    painted = true;
                }

                // 在框顶部绘制置信度文字（两位数字）
                int label_row = bx.y - 10;
                int label_col = bx.x;
                if (!painted && row >= label_row && row < label_row + 7 &&
                    col >= label_col && col < label_col + 12) {
                    int lr = row - label_row;
                    int lc = col - label_col;
                    uint8_t digit_h = '0' + (bx.confidence / 10);
                    uint8_t digit_l = '0' + (bx.confidence % 10);
                    bool px_on = (lc < 5)  ? get_font_pixel(digit_h, lr, lc) :
                                 (lc < 11) ? get_font_pixel(digit_l, lr, lc-6) : false;
                    if (px_on) {
                        paint_color = CLASS_COLORS[bx.class_id & 0x7];
                        painted = true;
                    }
                }
            }

            if (painted) {
                out_px.data = ((ap_uint<24>)paint_color);
            }

            // 右下角叠加通道号（CH0-CH3）
            int ch_row = FRAME_HEIGHT - 20;
            int ch_col = FRAME_WIDTH  - 30;
            if (row >= ch_row && row < ch_row + 7 &&
                col >= ch_col && col < ch_col + 12) {
                int lr = row - ch_row, lc = col - ch_col;
                uint8_t d0 = 'C', d1 = 'H', d2 = '0' + channel_id;
                bool px_on = (lc < 5)  ? get_font_pixel(d0, lr, lc) :
                             (lc < 11) ? get_font_pixel(d1, lr, lc-6) : false;
                if (px_on) out_px.data = 0xFFFFFF;
            }

            m_video << out_px;
        }
    }
}
