#!/bin/bash
# ─────────────────────────────────────────────────────────
# EdgeVision-T1 仿真环境一键配置脚本
# 支持：x86_64 Linux / AArch64 Linux (ZCU102 PetaLinux)
#
# 用法：
#   sudo bash scripts/setup_sim_env.sh          # 完整安装
#   bash   scripts/setup_sim_env.sh --no-sudo   # 仅用户级安装
# ─────────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[SETUP]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN] ${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

NO_SUDO=0
for arg in "$@"; do [ "$arg" = "--no-sudo" ] && NO_SUDO=1; done

ARCH=$(uname -m)
log "系统架构: ${ARCH}"
log "项目根目录: ${PROJECT_ROOT}"

# ─── 1. Python 依赖 ─────────────────────────────────────
log "安装 Python 依赖..."

REQUIREMENTS="${PROJECT_ROOT}/sim/requirements.txt"
cat > "${REQUIREMENTS}" << 'EOF'
numpy>=1.21
opencv-python-headless>=4.5
paho-mqtt>=1.6
onnxruntime>=1.14;platform_machine!="aarch64"
# AArch64 需要单独安装 onnxruntime-linux-aarch64
EOF

if command -v pip3 &>/dev/null; then
    pip3 install --user -r "${REQUIREMENTS}" 2>&1 | tail -5
    log "Python 依赖安装完成"
elif command -v pip &>/dev/null; then
    pip install --user -r "${REQUIREMENTS}" 2>&1 | tail -5
    log "Python 依赖安装完成"
else
    warn "未找到 pip，请手动安装: numpy opencv-python-headless paho-mqtt"
fi

# AArch64 (ZCU102) 单独安装 onnxruntime
if [ "${ARCH}" = "aarch64" ]; then
    log "AArch64: 尝试安装 onnxruntime-linux-aarch64..."
    pip3 install --user onnxruntime 2>/dev/null || \
    warn "onnxruntime 未安装，将使用 MockDetector（无影响）"
fi

# ─── 2. 系统依赖（可选）─────────────────────────────────
if [ $NO_SUDO -eq 0 ] && command -v apt-get &>/dev/null; then
    log "安装系统依赖..."
    apt-get install -y -q \
        mosquitto mosquitto-clients \
        can-utils \
        iproute2 \
        python3-dev \
        libopencv-dev 2>/dev/null || warn "部分系统依赖安装失败（可选）"
fi

# ─── 3. 配置 vcan0（虚拟CAN）────────────────────────────
log "配置 vcan0 虚拟 CAN 接口..."

setup_vcan() {
    if ip link show vcan0 &>/dev/null; then
        log "vcan0 已存在"
        return
    fi
    if [ $NO_SUDO -eq 0 ]; then
        modprobe vcan 2>/dev/null || warn "vcan 内核模块不可用"
        ip link add dev vcan0 type vcan 2>/dev/null || true
        ip link set up vcan0 2>/dev/null || warn "vcan0 启动失败（无根权限或不支持）"
        ip link show vcan0 &>/dev/null && log "vcan0 已配置" || warn "vcan0 不可用，CAN测试将跳过"
    else
        warn "跳过 vcan0 配置（需要 root 权限）"
    fi
}
setup_vcan

# ─── 4. 启动本地 MQTT broker（可选）──────────────────────
log "配置本地 MQTT broker..."
MQTT_CONF="/tmp/mosquitto_sim.conf"
cat > "${MQTT_CONF}" << 'EOF'
# EdgeVision-T1 仿真 MQTT 配置
listener 1883 127.0.0.1
allow_anonymous true
log_type error
log_type warning
EOF

if command -v mosquitto &>/dev/null; then
    # 检查是否已运行
    if ! pgrep -x mosquitto &>/dev/null; then
        mosquitto -c "${MQTT_CONF}" -d 2>/dev/null && \
            log "mosquitto 已启动（localhost:1883）" || \
            warn "mosquitto 启动失败（仿真仍可运行，但无MQTT）"
    else
        log "mosquitto 已在运行"
    fi
else
    warn "mosquitto 未安装，MQTT 功能不可用（仿真不受影响）"
fi

# ─── 5. 创建仿真输出目录 ────────────────────────────────
mkdir -p "${PROJECT_ROOT}/sim_output/frames"
mkdir -p "${PROJECT_ROOT}/sim_output/reports"
log "仿真输出目录: ${PROJECT_ROOT}/sim_output/"

# ─── 6. 验证环境 ─────────────────────────────────────────
log "验证仿真环境..."
cd "${PROJECT_ROOT}"

python3 -c "
import sys, importlib
modules = [('numpy', '1.21'), ('cv2', '4.0'), ('paho.mqtt.client', '0')]
ok = True
for mod, ver in modules:
    try:
        m = importlib.import_module(mod)
        print(f'  ✓ {mod}')
    except ImportError:
        print(f'  ✗ {mod} (未安装)')
        if mod != 'paho.mqtt.client':
            ok = False
try:
    import onnxruntime as ort
    print(f'  ✓ onnxruntime ({ort.__version__})')
except ImportError:
    print('  ○ onnxruntime (未安装，将使用 MockDetector)')
sys.exit(0 if ok else 1)
"

log "运行场景生成器快速测试..."
python3 -c "
import sys
sys.path.insert(0, 'sim')
from scene_generator import SceneGenerator
gen = SceneGenerator()
frame, gt = gen.next_frame()
assert frame.shape == (480, 640, 3), f'帧尺寸错误: {frame.shape}'
print('  ✓ 场景生成器正常')
"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN} 仿真环境配置完成！${NC}"
echo ""
echo "  运行仿真：   bash scripts/run_full_sim.sh"
echo "  运行测试：   python3 tests/e2e_integration.py -v"
echo "  手动运行：   python3 sim/traffic_sim.py --frames 300 --fast"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
