#!/usr/bin/env python3
# @req ARCHITECTURE-§3
# @author sw-hw-toolflow-team | @since 2026-06-04 | @version 1.0
# @status verified
"""
工具流主入口 sw-htf
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog='sw-htf',
        description='软硬件协同开发工具流（sw_hw_toolflow）',
    )
    sub = parser.add_subparsers(dest='cmd', required=True)

    # 各子命令占位（具体实现见 sw_hw_toolflow/cli/）
    for name in ['trace', 'verify', 'build', 'sim', 'codegen', 'ai', 'release', 'toolchain', 'init']:
        p = sub.add_parser(name, help=f'{name} 子命令')
        p.add_argument('rest', nargs=argparse.REMAINDER)

    args = parser.parse_args()
    print(f'sw-htf {args.cmd} {" ".join(args.rest or [])}')
    print('（占位实现，请见 sw_hw_toolflow/cli/）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
