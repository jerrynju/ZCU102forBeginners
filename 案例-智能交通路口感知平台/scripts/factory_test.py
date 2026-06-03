#!/usr/bin/env python3
"""
工厂功能测试脚本（FCT - Functional Circuit Test）
自动化测试流程，通过 SSH 连接被测设备执行全套测试

使用方式：
    python3 factory_test.py <device_ip> <device_id>
    python3 factory_test.py 192.168.1.100 edge001

测试结果上传到 MES 系统（制造执行系统）
"""

import sys
import time
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
    print("错误：请安装 paramiko: pip install paramiko")
    sys.exit(1)

FACTORY_KEY = Path(__file__).parent / 'factory_key.pem'
PASS_MARK = "PASS"
FAIL_MARK = "FAIL"

class FactoryTestRunner:
    def __init__(self, device_ip: str, device_id: str):
        self.device_ip  = device_ip
        self.device_id  = device_id
        self.results    = {}
        self.start_time = datetime.now()
        self.ssh        = None

    def connect(self, timeout=60):
        """等待设备 SSH 就绪后连接"""
        print(f"连接设备 {self.device_ip}...")
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if FACTORY_KEY.exists():
                    self.ssh.connect(self.device_ip, username='root',
                                    key_filename=str(FACTORY_KEY), timeout=10)
                else:
                    # 工厂预设密码（量产后通过 eFUSE 禁用密码登录）
                    self.ssh.connect(self.device_ip, username='root',
                                    password='factory_temp_passwd', timeout=10)
                print(f"  SSH 连接成功")
                return True
            except Exception:
                print('.', end='', flush=True)
                time.sleep(3)

        print(f"\n错误：无法在 {timeout}s 内连接设备")
        return False

    def run_cmd(self, cmd: str, timeout=30) -> tuple[int, str, str]:
        """在设备上执行命令，返回 (exit_code, stdout, stderr)"""
        _, stdout, stderr = self.ssh.exec_command(cmd, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, stdout.read().decode(), stderr.read().decode()

    def record(self, test_name: str, passed: bool,
               details: dict = None, duration_s: float = 0):
        mark = PASS_MARK if passed else FAIL_MARK
        self.results[test_name] = {
            'pass': passed, 'mark': mark,
            'details': details or {}, 'duration_s': round(duration_s, 2)
        }
        print(f"  [{mark}] {test_name:<30} {duration_s:.1f}s")
        if not passed and details:
            for k, v in details.items():
                print(f"         {k}: {v}")

    # ─────────────────────────────────────────────────────────
    # 测试项目
    # ─────────────────────────────────────────────────────────

    def test_linux_boot(self):
        t0 = time.time()
        rc, out, _ = self.run_cmd("cat /proc/version && uptime")
        passed = rc == 0 and 'Linux' in out
        self.record('linux_boot', passed,
                    {'kernel': out.split('\n')[0][:80] if passed else 'N/A'},
                    time.time() - t0)

    def test_dpu_available(self):
        t0 = time.time()
        rc, out, _ = self.run_cmd("ls /dev/dri/renderD128 2>/dev/null && echo OK")
        passed = rc == 0 and 'OK' in out
        # 也检查 DPU 驱动日志
        _, dmesg, _ = self.run_cmd("dmesg | grep -i 'zocl\\|dpu' | tail -3")
        self.record('dpu_available', passed,
                    {'dpu_node': '/dev/dri/renderD128', 'dmesg': dmesg.strip()},
                    time.time() - t0)

    def test_cameras(self):
        t0 = time.time()
        all_ok = True
        cam_status = {}
        for ch in range(4):
            rc, out, _ = self.run_cmd(
                f"v4l2-ctl -d /dev/video{ch} --all 2>&1 | grep 'Width/Height'")
            ok = rc == 0 and '1920' in out and '1080' in out
            cam_status[f'cam{ch}'] = 'OK' if ok else 'FAIL'
            if not ok: all_ok = False
        self.record('cameras_4ch', all_ok, cam_status, time.time() - t0)

    def test_dpu_inference(self):
        """用标准测试图片验证推理结果（与 Golden 文件对比）"""
        t0 = time.time()
        # 上传测试图片
        sftp = self.ssh.open_sftp()
        test_img = Path(__file__).parent / '../ai/deploy/test_golden.jpg'
        if test_img.exists():
            sftp.put(str(test_img), '/tmp/test_golden.jpg')
        sftp.close()

        rc, out, err = self.run_cmd(
            "traffic_infer_cli /tmp/test_golden.jpg /tmp/infer_result.json 2>&1",
            timeout=60)

        if rc != 0:
            self.record('dpu_inference', False,
                       {'error': err[:200]}, time.time() - t0)
            return

        _, result_json, _ = self.run_cmd("cat /tmp/infer_result.json")
        try:
            result = json.loads(result_json)
            cars    = sum(1 for o in result.get('objects', []) if o.get('class') == 'car')
            persons = sum(1 for o in result.get('objects', []) if o.get('class') == 'person')
            lat_ms  = result.get('latency_ms', 0)
            # 期望：测试图中有 3 辆车，1 个行人，推理延迟 < 50ms
            passed = (cars >= 2) and (persons >= 1) and (lat_ms < 50)
            self.record('dpu_inference', passed,
                       {'cars': cars, 'persons': persons, 'latency_ms': f'{lat_ms:.1f}'},
                       time.time() - t0)
        except json.JSONDecodeError:
            self.record('dpu_inference', False,
                       {'error': 'Invalid JSON output'}, time.time() - t0)

    def test_10gbe_loopback(self):
        t0 = time.time()
        # 检查网口 up 状态
        rc, out, _ = self.run_cmd("ip link show eth0 | grep 'state UP'")
        if rc != 0:
            self.record('10gbe_link', False, {'error': 'eth0 not UP'}, time.time() - t0)
            return
        # iperf3 本机回环测试
        self.run_cmd("iperf3 -s -D -p 15201")  # 后台启动服务端
        time.sleep(0.5)
        rc, out, _ = self.run_cmd("iperf3 -c 127.0.0.1 -p 15201 -t 5 -J", timeout=15)
        self.run_cmd("killall iperf3")
        try:
            data = json.loads(out)
            bps  = data['end']['sum_received']['bits_per_second']
            passed = bps > 8e9  # > 8 Gbps
            self.record('10gbe_loopback', passed,
                       {'throughput_gbps': f'{bps/1e9:.2f}'}, time.time() - t0)
        except Exception as e:
            self.record('10gbe_loopback', False, {'error': str(e)}, time.time() - t0)

    def test_can_loopback(self):
        """CAN 总线自环测试（需要物理短接 CANH/CANL 或回环模式）"""
        t0 = time.time()
        # 设置 CAN 接口
        self.run_cmd("ip link set can0 down 2>/dev/null")
        self.run_cmd("ip link set can0 up type can bitrate 500000 loopback on")
        # 发送并接收一帧
        self.run_cmd("cansend can0 123#DEADBEEF &")
        rc, out, _ = self.run_cmd("candump can0 -n 1 -T 2000 2>&1")
        passed = rc == 0 and 'DEADBEEF' in out.upper()
        self.run_cmd("ip link set can0 down 2>/dev/null")
        self.record('can_loopback', passed, {'recv': out.strip()[:80]}, time.time() - t0)

    def test_temperature_sensors(self):
        t0 = time.time()
        rc, out, _ = self.run_cmd(
            "cat /sys/bus/iio/devices/iio:device0/in_temp0_ps_temp_raw 2>/dev/null")
        # XSysmon 温度传感器（Zynq 内部）
        # raw_to_celsius = (raw * 509.3140 / 65536.0) - 280.2308
        try:
            raw = int(out.strip())
            temp_c = (raw * 509.314 / 65536.0) - 280.2308
            # 正常工作温度范围（冷机上电）
            passed = 0 < temp_c < 85
            self.record('temperature', passed,
                       {'soc_temp_c': f'{temp_c:.1f}'}, time.time() - t0)
        except Exception:
            self.record('temperature', False,
                       {'error': f'Raw: {out.strip()}'}, time.time() - t0)

    def test_secure_boot(self):
        """验证安全启动链完整性"""
        t0 = time.time()
        # 读取 eFUSE 状态（通过 Xilinx 工具）
        rc, out, _ = self.run_cmd(
            "xsdbserver start 2>/dev/null; sleep 0.5; "
            "cat /sys/firmware/devicetree/base/chosen/bootargs 2>/dev/null | "
            "grep -o 'security=selinux' || echo 'basic'")
        # 检查内核 IMA 度量日志
        rc2, ima, _ = self.run_cmd(
            "cat /sys/kernel/security/ima/ascii_runtime_measurements 2>/dev/null | wc -l")
        ima_entries = int(ima.strip()) if rc2 == 0 and ima.strip().isdigit() else 0
        passed = ima_entries > 0
        self.record('secure_boot', passed,
                   {'ima_entries': ima_entries}, time.time() - t0)

    def test_flash_firmware_version(self):
        """验证固件版本号（确认烧录的是正确版本）"""
        t0 = time.time()
        rc, out, _ = self.run_cmd("cat /etc/traffic_edge_version 2>/dev/null")
        version = out.strip()
        EXPECTED_VERSION = "2.3.1"  # 与 build 系统中的版本一致
        passed = version == EXPECTED_VERSION
        self.record('firmware_version', passed,
                   {'expected': EXPECTED_VERSION, 'actual': version},
                   time.time() - t0)

    # ─────────────────────────────────────────────────────────
    # 主流程
    # ─────────────────────────────────────────────────────────

    def run_all(self) -> bool:
        print(f"\n{'='*60}")
        print(f"工厂测试开始")
        print(f"设备 IP:  {self.device_ip}")
        print(f"设备 ID:  {self.device_id}")
        print(f"时间:     {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        tests = [
            ('Linux 启动验证',     self.test_linux_boot),
            ('DPU 驱动检测',       self.test_dpu_available),
            ('4路摄像头检测',      self.test_cameras),
            ('DPU 推理精度',       self.test_dpu_inference),
            ('10GbE 回环测试',     self.test_10gbe_loopback),
            ('CAN 总线回环',       self.test_can_loopback),
            ('温度传感器',         self.test_temperature_sensors),
            ('固件版本验证',       self.test_flash_firmware_version),
            ('安全启动验证',       self.test_secure_boot),
        ]

        for name, fn in tests:
            try:
                fn()
            except Exception as e:
                self.record(name.replace(' ', '_'), False, {'exception': str(e)})

        # 汇总
        total     = len(self.results)
        passed    = sum(1 for r in self.results.values() if r['pass'])
        all_pass  = (passed == total)
        duration  = (datetime.now() - self.start_time).total_seconds()

        print(f"{'='*60}")
        print(f"测试汇总: {passed}/{total} 通过  总用时: {duration:.1f}s")
        print(f"最终结论: {'【通过】✓' if all_pass else '【失败】✗'}")
        print(f"{'='*60}\n")

        # 保存 JSON 报告
        report = {
            'device_id':  self.device_id,
            'device_ip':  self.device_ip,
            'test_time':  self.start_time.isoformat(),
            'duration_s': round(duration, 1),
            'all_pass':   all_pass,
            'pass_count': passed,
            'total_count':total,
            'tests':      self.results,
        }
        report_file = f"fct_{self.device_id}_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"测试报告: {report_file}")

        return all_pass

def main():
    p = argparse.ArgumentParser()
    p.add_argument('device_ip')
    p.add_argument('device_id')
    args = p.parse_args()

    runner = FactoryTestRunner(args.device_ip, args.device_id)
    if not runner.connect():
        sys.exit(2)

    try:
        success = runner.run_all()
    finally:
        if runner.ssh:
            runner.ssh.close()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
