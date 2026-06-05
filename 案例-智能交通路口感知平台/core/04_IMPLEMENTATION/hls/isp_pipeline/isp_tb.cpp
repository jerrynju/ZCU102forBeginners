// @req SYS-REQ-001, PERF-REQ-001
// @design DES-ARCH-007
// @test TC-CAM-001
// @author fpga-team | @since 2026-06-04 | @version 1.0
// @status verified
//
// MOD-HLS-ISP: C 测试平台
// 从 BMP/RAW 文件读入 RAW10 图像，运行 ISP，输出 NV12 与参考对比

#include "isp_pipeline.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define PSNR_THRESHOLD 35.0  // dB，低于此值视为测试失败

// 读取 16bit raw 文件（RAW10 打包在 16bit 中）
static uint16_t raw_in[SRC_HEIGHT][SRC_WIDTH];
static uint8_t  nv12_out[DST_HEIGHT * 3 / 2][DST_WIDTH];
static uint8_t  nv12_ref[DST_HEIGHT * 3 / 2][DST_WIDTH];  // Golden reference

bool load_raw_image(const char* filename) {
    FILE* f = fopen(filename, "rb");
    if (!f) { printf("Cannot open %s\n", filename); return false; }
    size_t n = fread(raw_in, sizeof(uint16_t), SRC_HEIGHT * SRC_WIDTH, f);
    fclose(f);
    return n == (size_t)(SRC_HEIGHT * SRC_WIDTH);
}

bool load_reference(const char* filename) {
    FILE* f = fopen(filename, "rb");
    if (!f) { printf("Cannot open reference %s\n", filename); return false; }
    size_t n = fread(nv12_ref, 1, DST_HEIGHT * 3 / 2 * DST_WIDTH, f);
    fclose(f);
    return n == (size_t)(DST_HEIGHT * 3 / 2 * DST_WIDTH);
}

double calc_psnr(uint8_t* a, uint8_t* b, int len) {
    double mse = 0;
    for (int i = 0; i < len; i++) {
        double diff = (double)a[i] - (double)b[i];
        mse += diff * diff;
    }
    mse /= len;
    if (mse == 0) return 100.0;
    return 10.0 * log10(255.0 * 255.0 / mse);
}

int main(int argc, char* argv[]) {
    printf("=== ISP Pipeline HLS Testbench ===\n");
    printf("Input:  %d x %d RAW10 Bayer (RGGB)\n", SRC_WIDTH, SRC_HEIGHT);
    printf("Output: %d x %d NV12\n", DST_WIDTH, DST_HEIGHT);

    // 1. 加载测试图像
    const char* raw_file = (argc > 1) ? argv[1] : "test_raw_4k.raw";
    const char* ref_file = (argc > 2) ? argv[2] : "test_ref_1080p.nv12";

    if (!load_raw_image(raw_file)) {
        printf("Generating synthetic test pattern...\n");
        // 生成 Bayer 格式测试图（灰阶阶梯 + 彩色格子）
        for (int r = 0; r < SRC_HEIGHT; r++)
            for (int c = 0; c < SRC_WIDTH; c++)
                raw_in[r][c] = (uint16_t)((r * 64 + c) & 0x3FF);  // 10bit
    }

    // 2. 构建 AXI-Stream 输入
    AXIS_IN  axis_in;
    AXIS_OUT axis_out;

    for (int r = 0; r < SRC_HEIGHT; r++) {
        for (int c = 0; c < SRC_WIDTH; c++) {
            AXI_PIX_IN px;
            px.data = raw_in[r][c];
            px.keep = 1; px.strb = 1;
            px.last = (r == SRC_HEIGHT-1 && c == SRC_WIDTH-1) ? 1 : 0;
            axis_in << px;
        }
    }

    // 3. 运行 ISP（默认参数：黑电平 64，白平衡均等，RGGB）
    printf("Running ISP pipeline...\n");
    isp_pipeline(
        axis_in, axis_out,
        64,    // black_level
        256,   // wb_gain_r  (1.0x)
        256,   // wb_gain_g
        280,   // wb_gain_b  (1.09x，轻微蓝色补偿)
        0      // bayer_pattern: RGGB
    );

    // 4. 收集输出
    int out_idx = 0;
    while (!axis_out.empty()) {
        AXI_PIX_OUT px;
        axis_out >> px;
        if (out_idx < DST_HEIGHT * 3 / 2 * DST_WIDTH)
            nv12_out[out_idx / DST_WIDTH][out_idx % DST_WIDTH] = px.data;
        out_idx++;
    }
    printf("Output bytes: %d (expected %d)\n",
           out_idx, DST_HEIGHT * 3 / 2 * DST_WIDTH);

    // 5. 保存输出文件
    FILE* fo = fopen("isp_output.nv12", "wb");
    if (fo) {
        fwrite(nv12_out, 1, DST_HEIGHT * 3 / 2 * DST_WIDTH, fo);
        fclose(fo);
        printf("Output saved to isp_output.nv12\n");
    }

    // 6. 与参考对比
    int pass = 1;
    if (load_reference(ref_file)) {
        int y_len  = DST_HEIGHT * DST_WIDTH;
        int uv_len = DST_HEIGHT / 2 * DST_WIDTH;
        double psnr_y  = calc_psnr(&nv12_out[0][0], &nv12_ref[0][0], y_len);
        double psnr_uv = calc_psnr(&nv12_out[DST_HEIGHT][0],
                                   &nv12_ref[DST_HEIGHT][0], uv_len);
        printf("PSNR Y:  %.2f dB (threshold %.1f dB) %s\n",
               psnr_y, PSNR_THRESHOLD, psnr_y >= PSNR_THRESHOLD ? "PASS" : "FAIL");
        printf("PSNR UV: %.2f dB (threshold %.1f dB) %s\n",
               psnr_uv, PSNR_THRESHOLD, psnr_uv >= PSNR_THRESHOLD ? "PASS" : "FAIL");
        pass = (psnr_y >= PSNR_THRESHOLD) && (psnr_uv >= PSNR_THRESHOLD);
    } else {
        printf("No reference file, skipping PSNR check.\n");
        // 基本完整性检查
        int total = DST_HEIGHT * 3 / 2 * DST_WIDTH;
        pass = (out_idx == total);
        printf("Output byte count: %s\n", pass ? "PASS" : "FAIL");
    }

    printf("\n=== Testbench %s ===\n", pass ? "PASSED" : "FAILED");
    return pass ? 0 : 1;
}
