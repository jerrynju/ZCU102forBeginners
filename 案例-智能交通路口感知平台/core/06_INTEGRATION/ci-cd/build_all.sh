#!/bin/bash
# @req DES-ARCH-001, DES-ARCH-002, PERF-REQ-004, VP-002, VP-003
# @design DES-ARCH-001
# @test TC-CAM-001, TC-AI-DET-001, TC-PERF-DPU-001
# @author build-team | @since 2026-06-04 | @version 1.0
# @status verified
#
# 完整构建脚本：从源码到可烧录镜像

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
VIVADO_VERSION="2023.1"
PETALINUX_VERSION="2023.1"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

# ── 检查工具链 ────────────────────────────────────────────
check_tools() {
    log "Checking toolchain..."
    command -v vivado     &>/dev/null || die "Vivado not found. Source settings64.sh"
    command -v vitis_hls  &>/dev/null || die "Vitis HLS not found"
    command -v petalinux-build &>/dev/null || die "PetaLinux not found. Source settings.sh"
    command -v vai_c_xir  &>/dev/null || die "Vitis AI compiler not found"
    log "All tools found."
}

# ── 步骤 1：HLS IP 综合 ────────────────────────────────────
build_hls_ips() {
    log "Step 1/5: Synthesizing HLS IPs..."
    for ip in isp_pipeline osd_overlay; do
        vitis_hls -f "$PROJECT_ROOT/hardware/hls/$ip/run_hls.tcl" \
            || die "HLS synthesis failed for $ip"
        log "  ✓ $ip synthesized"
    done
}

# ── 步骤 2：Vivado 综合实现 ────────────────────────────────
build_vivado() {
    log "Step 2/5: Running Vivado synthesis and implementation..."
    mkdir -p "$BUILD_DIR/vivado"
    vivado -mode batch -source "$PROJECT_ROOT/hardware/vivado_project/build.tcl" \
        -tclargs "$BUILD_DIR/vivado" \
        || die "Vivado build failed"
    # 检查时序是否收敛（WNS >= 0）
    python3 "$SCRIPT_DIR/check_timing.py" \
        "$BUILD_DIR/vivado/timing_summary.rpt" \
        || die "Timing not met! Check timing report."
    log "  ✓ Bitstream generated: $BUILD_DIR/vivado/traffic_edge.bit"
    # 导出 XSA
    vivado -mode batch \
        -source "$SCRIPT_DIR/export_xsa.tcl" \
        -tclargs "$BUILD_DIR/vivado"
    log "  ✓ XSA exported: $BUILD_DIR/vivado/traffic_edge.xsa"
}

# ── 步骤 3：PetaLinux 构建 ────────────────────────────────
build_petalinux() {
    log "Step 3/5: Building PetaLinux..."
    cd "$PROJECT_ROOT/software/petalinux/traffic_edge"
    petalinux-config --get-hw-description="$BUILD_DIR/vivado/traffic_edge.xsa" \
        --silentconfig
    petalinux-build -j$(nproc) || die "PetaLinux build failed"
    petalinux-package --boot \
        --fsbl "./images/linux/zynqmp_fsbl.elf" \
        --fpga "$BUILD_DIR/vivado/traffic_edge.bit" \
        --u-boot --pmufw --atf --force
    cp images/linux/BOOT.BIN  "$BUILD_DIR/"
    cp images/linux/image.ub  "$BUILD_DIR/"
    cp images/linux/rootfs.ext4 "$BUILD_DIR/"
    log "  ✓ Linux images built"
}

# ── 步骤 4：AI 模型量化编译 ───────────────────────────────
build_ai_models() {
    log "Step 4/5: Quantizing and compiling AI models..."
    # 需要在 Vitis AI Docker 容器内运行，此处假设已配置环境
    cd "$PROJECT_ROOT/ai"
    python3 quantization/ptq_quantize.py \
        --model weights/yolov8s_traffic.onnx \
        --calib-data data/calib \
        --output "$BUILD_DIR/models/yolov8s_int8.xmodel" \
        || die "Quantization failed"
    vai_c_xir \
        -x "$BUILD_DIR/models/yolov8s_int8.xmodel" \
        -a /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU102/arch.json \
        -o "$BUILD_DIR/models/" \
        -n yolov8s_traffic \
        || die "Model compilation failed"
    log "  ✓ Models compiled: $BUILD_DIR/models/"
}

# ── 步骤 5：打包发布 ──────────────────────────────────────
package_release() {
    log "Step 5/5: Packaging release..."
    VERSION=$(cat "$PROJECT_ROOT/VERSION")
    RELEASE_DIR="$BUILD_DIR/release_v${VERSION}"
    mkdir -p "$RELEASE_DIR"
    cp "$BUILD_DIR/BOOT.BIN"    "$RELEASE_DIR/"
    cp "$BUILD_DIR/image.ub"    "$RELEASE_DIR/"
    cp "$BUILD_DIR/rootfs.ext4" "$RELEASE_DIR/"
    cp -r "$BUILD_DIR/models/"  "$RELEASE_DIR/models/"
    cp "$SCRIPT_DIR/flash_device.sh" "$RELEASE_DIR/"
    # 生成 SHA256 校验文件
    cd "$RELEASE_DIR"
    sha256sum BOOT.BIN image.ub rootfs.ext4 > SHA256SUMS
    # 打包
    cd "$BUILD_DIR"
    tar czf "traffic_edge_v${VERSION}.tar.gz" "release_v${VERSION}/"
    log "  ✓ Release package: $BUILD_DIR/traffic_edge_v${VERSION}.tar.gz"
}

# ── 主流程 ────────────────────────────────────────────────
main() {
    log "=== TrafficEdge Build System ==="
    log "Project: $PROJECT_ROOT"
    check_tools
    build_hls_ips
    build_vivado
    build_petalinux
    build_ai_models
    package_release
    log "=== Build Complete ==="
}

main "$@"
