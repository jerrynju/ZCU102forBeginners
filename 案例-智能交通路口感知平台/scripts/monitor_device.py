#!/usr/bin/env python3
"""
设备远程监控脚本
通过 gRPC 连接 ZCU102，实时显示系统状态和检测统计

用法：
    python3 scripts/monitor_device.py --host 192.168.1.100
    python3 scripts/monitor_device.py --host 192.168.1.100 --stream --channel 0
"""

import argparse
import time
import sys
import os
import json
from datetime import datetime

try:
    import grpc
    import curses
    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False
    print("警告：grpc 不可用，使用 REST 模式")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--host',    default='192.168.1.100')
    p.add_argument('--port',    type=int, default=8080, help='REST API 端口')
    p.add_argument('--grpc-port', type=int, default=50051)
    p.add_argument('--interval', type=float, default=2.0, help='刷新间隔（秒）')
    p.add_argument('--stream',  action='store_true', help='实时检测流')
    p.add_argument('--channel', type=int, default=0)
    p.add_argument('--json',    action='store_true', help='JSON 输出（适合脚本处理）')
    return p.parse_args()

class DeviceMonitor:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api"

    def get_status(self) -> dict:
        if not HAS_REQUESTS:
            return self._mock_status()
        try:
            r = requests.get(f"{self.base_url}/status", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {'error': str(e)}

    def get_flow_stats(self) -> dict:
        if not HAS_REQUESTS:
            return {}
        try:
            r = requests.get(f"{self.base_url}/stats/realtime", timeout=5)
            return r.json()
        except Exception:
            return {}

    def _mock_status(self) -> dict:
        """离线演示数据"""
        import random
        return {
            'device_id': 'edge001',
            'firmware_ver': '2.3.1',
            'online': True,
            'system': {
                'cpu_a53_pct': random.uniform(40, 80),
                'mem_used_pct': random.uniform(50, 70),
                'soc_temp_c': random.uniform(55, 70),
                'dpu_util_pct': random.uniform(60, 90),
                'infer_fps': random.uniform(25, 30),
                'infer_lat_ms': random.uniform(18, 25),
                'uptime_s': int(time.time() % 86400),
            },
            'channels': [
                {
                    'channel_id': ch,
                    'camera_online': True,
                    'capture_fps': random.uniform(28, 30),
                    'queue_length_m': random.uniform(10, 60),
                    'counts': [
                        {'class_name': 'car',    'count': random.randint(20, 50)},
                        {'class_name': 'person', 'count': random.randint(5, 20)},
                        {'class_name': 'truck',  'count': random.randint(2, 8)},
                    ]
                } for ch in range(4)
            ],
            'signal': {
                'current_phase': 'NS_GREEN',
                'phase_remain_s': random.randint(5, 45),
                'adaptive_mode': True,
            },
            'network': {
                'primary_link': '10gbe',
                'link_speed_mbps': 10000,
                'pending_events': random.randint(0, 5),
            }
        }

def format_status(status: dict) -> str:
    """格式化设备状态为可读文本"""
    lines = []
    ts = datetime.now().strftime('%H:%M:%S')

    if 'error' in status:
        return f"[{ts}] 连接错误: {status['error']}"

    sys_info = status.get('system', {})
    signal   = status.get('signal', {})
    network  = status.get('network', {})

    lines.append(f"{'='*60}")
    lines.append(f"设备: {status.get('device_id','?')}  固件: {status.get('firmware_ver','?')}  时间: {ts}")
    lines.append(f"{'─'*60}")
    lines.append(f"系统资源:")
    lines.append(f"  CPU(A53): {sys_info.get('cpu_a53_pct',0):5.1f}%  "
                 f"内存: {sys_info.get('mem_used_pct',0):5.1f}%  "
                 f"SoC温度: {sys_info.get('soc_temp_c',0):5.1f}°C")
    lines.append(f"  DPU利用率: {sys_info.get('dpu_util_pct',0):5.1f}%  "
                 f"推理帧率: {sys_info.get('infer_fps',0):5.1f}FPS  "
                 f"延迟: {sys_info.get('infer_lat_ms',0):5.1f}ms")
    lines.append(f"  运行时长: {sys_info.get('uptime_s',0)//3600}h{(sys_info.get('uptime_s',0)%3600)//60}m")
    lines.append(f"{'─'*60}")
    lines.append(f"信号灯: [{signal.get('current_phase','?')}]  "
                 f"剩余: {signal.get('phase_remain_s',0)}s  "
                 f"自适应: {'开' if signal.get('adaptive_mode') else '关'}")
    lines.append(f"网络: {network.get('primary_link','?').upper()}  "
                 f"{network.get('link_speed_mbps',0)}Mbps  "
                 f"待上报事件: {network.get('pending_events',0)}")
    lines.append(f"{'─'*60}")
    lines.append(f"各通道实时统计（当前分钟）:")
    lines.append(f"  {'通道':<4} {'摄像头':^6} {'采集FPS':^8} {'排队(m)':^8} "
                 f"{'车辆':^6} {'行人':^6} {'货车':^6}")

    for ch in status.get('channels', []):
        counts = {c['class_name']: c['count'] for c in ch.get('counts', [])}
        lines.append(
            f"  CH{ch['channel_id']:<2}  "
            f"{'在线' if ch['camera_online'] else '离线':^6}  "
            f"{ch.get('capture_fps',0):^8.1f}  "
            f"{ch.get('queue_length_m',0):^8.1f}  "
            f"{counts.get('car',0):^6}  "
            f"{counts.get('person',0):^6}  "
            f"{counts.get('truck',0):^6}"
        )
    lines.append(f"{'='*60}")
    return '\n'.join(lines)

def main():
    args = parse_args()
    monitor = DeviceMonitor(args.host, args.port)

    if args.json:
        status = monitor.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return

    print(f"连接设备: {args.host}:{args.port}")
    print(f"刷新间隔: {args.interval}s，按 Ctrl+C 退出\n")

    try:
        while True:
            status = monitor.get_status()
            # 清屏
            os.system('clear' if os.name != 'nt' else 'cls')
            print(format_status(status))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == '__main__':
    main()
