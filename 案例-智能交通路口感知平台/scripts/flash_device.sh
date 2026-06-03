#!/bin/bash
# 设备烧录脚本（通过 SD 卡或 JTAG）

set -euo pipefail

DEVICE_IP="${1:-}"
MODE="${2:-sd}"  # sd | jtag | ota

usage() {
    echo "Usage: $0 <device_ip> [sd|jtag|ota]"
    echo "  sd:   Boot from SD card, then flash to eMMC"
    echo "  jtag: Flash via Xilinx JTAG (device in JTAG mode)"
    echo "  ota:  Push OTA update to running device"
    exit 1
}

[ -z "$DEVICE_IP" ] && usage

flash_via_sd() {
    # 1. 将镜像写入 SD 卡
    SD_DEVICE="${SD_DEVICE:-/dev/sdb}"
    echo "Writing boot files to SD card $SD_DEVICE..."
    sudo dd if=BOOT.BIN of="$SD_DEVICE" bs=512 seek=0 conv=sync
    sudo dd if=image.ub  of="$SD_DEVICE" bs=512 seek=8192 conv=sync

    # 2. 设备 SD 卡启动后，SSH 连接刷写 eMMC
    echo "Waiting for device to boot from SD card..."
    until ssh -o ConnectTimeout=5 root@"$DEVICE_IP" true 2>/dev/null; do
        sleep 5; echo -n "."
    done
    echo ""
    echo "Flashing eMMC..."
    ssh root@"$DEVICE_IP" << 'REMOTE'
        # 写入 eMMC Boot 分区
        dd if=/dev/mmcblk1 of=/dev/mmcblk0boot0 bs=512 count=8192 status=progress
        # 写入内核分区
        dd if=/dev/mmcblk1p1 of=/dev/mmcblk0p1 bs=4M status=progress
        # 写入根文件系统
        dd if=/dev/mmcblk1p2 of=/dev/mmcblk0p3 bs=4M status=progress
        sync
        echo "eMMC flash complete"
REMOTE
    echo "Reboot device and remove SD card."
}

flash_via_ota() {
    # 通过 SWUpdate HTTP 接口推送 OTA 包
    OTA_PACKAGE=$(ls traffic_edge_*.swu 2>/dev/null | sort -V | tail -1)
    [ -z "$OTA_PACKAGE" ] && { echo "No .swu package found"; exit 1; }
    echo "Pushing OTA package: $OTA_PACKAGE"
    curl --progress-bar \
         -F "file=@$OTA_PACKAGE" \
         "http://$DEVICE_IP:8080/api/ota/upload" \
         || { echo "OTA upload failed"; exit 1; }
    echo "OTA package uploaded. Device will reboot automatically."
    # 等待重启完成
    sleep 30
    until ssh -o ConnectTimeout=5 root@"$DEVICE_IP" \
              "cat /etc/traffic_edge_version" 2>/dev/null; do
        sleep 5; echo -n "."
    done
    echo "OTA complete!"
}

case "$MODE" in
    sd)   flash_via_sd ;;
    ota)  flash_via_ota ;;
    *)    usage ;;
esac
