#!/bin/bash

MAX_RETRY=30      # 最大重试次数
RETRY_DELAY=10   # 每次检测间隔秒数（秒）
FAIL_COUNT=0

echo "检测网络连接状态..."

# 连续检测 MAX_RETRY 次
for ((i=1; i<=MAX_RETRY; i++)); do
    if nmcli -t -f DEVICE,STATE dev | grep -q '^wlan0:connected$' \
        || ping -q -c 1 -W 2 114.114.114.114 >/dev/null; then
        echo "已连接网络（第 $i 次检测）"
        exit 0
    else
        echo "第 $i 次检测：无网络"
        FAIL_COUNT=$((FAIL_COUNT+1))
        sleep $RETRY_DELAY
    fi
done

# 如果连续 FAIL_COUNT 次失败，启动 WiFi Connect
if [ "$FAIL_COUNT" -ge "$MAX_RETRY" ]; then
    echo "连续 $FAIL_COUNT 次无网络，启动 WiFi Connect"
    /usr/local/sbin/wifi-connect --portal-ssid "$(hostname)_wifi connect"
fi

