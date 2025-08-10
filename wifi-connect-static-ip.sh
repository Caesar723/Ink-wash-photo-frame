#!/bin/bash

# 检查是否有有效网络连接（ping 一次 8.8.8.8，超时 2 秒）
if ping -q -c 1 -W 2 8.8.8.8 >/dev/null; then
    echo "已连接网络，跳过 WiFi Connect"
    exit 0
else
    echo "未连接网络，启动 WiFi Connect"
    /usr/local/sbin/wifi-connect --ssid "$(hostname)_wifi connect"
fi
