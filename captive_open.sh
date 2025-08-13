#!/usr/bin/env bash
set -euo pipefail

# ===== 可调参数 =====
IFACE="wlan0"
SSID="PiPortal-$(hostname)"   # 开放热点名
COUNTRY="CN"
GW_IP="192.168.4.1"
DHCP_START="192.168.4.50"
DHCP_END="192.168.4.200"
APP="/home/xuanpeichen/Desktop/Ink-wash-photo-frame/wifiManager/main.py"   # 你之前的 FastAPI 文件

log(){ echo -e "\033[1;32m[+] $*\033[0m"; }
err(){ echo -e "\033[1;31m[✗] $*\033[0m" >&2; }

install_deps(){
  apt update
  DEBIAN_FRONTEND=noninteractive apt install -y hostapd dnsmasq iptables-persistent
  raspi-config nonint do_wifi_country "$COUNTRY" || true
  iw reg set "$COUNTRY" || true
}

write_configs(){
  # 开放热点：**不写任何 WPA 相关项**
  cat >/etc/hostapd/hostapd.conf <<EOF
interface=${IFACE}
driver=nl80211
ssid=${SSID}
hw_mode=g
channel=6
ieee80211n=1
wmm_enabled=1
auth_algs=1
ignore_broadcast_ssid=0
country_code=${COUNTRY}
EOF
  echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >/etc/default/hostapd

  mkdir -p /etc/dnsmasq.d
  cat >/etc/dnsmasq.d/captive.conf <<EOF
interface=${IFACE}
bind-interfaces
no-resolv
server=114.114.114.114
server=223.5.5.5
# 强制门户：所有域名都指向树莓派
address=/#/${GW_IP}
# DHCP 池
dhcp-range=${DHCP_START},${DHCP_END},255.255.255.0,12h
dhcp-option=3,${GW_IP}
dhcp-option=6,${GW_IP}
EOF
}

start(){
  command -v hostapd >/dev/null || install_deps
  [ -f /etc/hostapd/hostapd.conf ] || write_configs
  [ -f "$APP" ] || { err "未找到 $APP ；请先放好 FastAPI 应用"; exit 1; }

  # 避免与 NM 抢网卡（如果你想保留 NM，后面我可给另一个变体）
  systemctl stop NetworkManager || true

  ip addr flush dev "$IFACE" || true
  ip addr add "${GW_IP}/24" dev "$IFACE"
  ip link set "$IFACE" up

  systemctl restart dnsmasq
  systemctl restart hostapd

  # 把 wlan0 上所有 HTTP 重定向到本机 80，实现“自动弹网页”
  iptables -t nat -C PREROUTING -i "$IFACE" -p tcp --dport 80 -j REDIRECT --to-ports 80 2>/dev/null \
    || iptables -t nat -A PREROUTING -i "$IFACE" -p tcp --dport 80 -j REDIRECT --to-ports 80

  #exec /home/xuanpeichen/myenv/bin/python3 "$APP"
}

stop(){
  #pkill -f "$APP" || true
  iptables -t nat -D PREROUTING -i "$IFACE" -p tcp --dport 80 -j REDIRECT --to-ports 80 2>/dev/null || true
  systemctl stop hostapd || true
  systemctl stop dnsmasq || true
  systemctl start NetworkManager || true
}

status(){
  systemctl is-active hostapd || true
  systemctl is-active dnsmasq || true
  ip -4 addr show "$IFACE" || true
  echo "NAT PREROUTING:"
  iptables -t nat -S PREROUTING | grep REDIRECT || true
}
get_sta_ip() {
  ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}')
  [ -n "$ip" ] || ip=$(nmcli -g IP4.ADDRESS device show "$IFACE" 2>/dev/null | head -n1 | cut -d/ -f1)
  echo "$ip"
}

start_app(){
  systemctl start NetworkManager
  SCAN_RESULTS="$(nmcli -t -f CHAN,SIGNAL,SSID dev wifi | grep -v '^$')"
  export WIFI_SCAN_RESULTS="$SCAN_RESULTS"
  #start
  exec /home/xuanpeichen/myenv/bin/python3 "$APP"
}
case "${1:-}" in
  setup)  install_deps; write_configs; echo "已写配置，运行：sudo $0 start" ;;
  start)  start ;;
  stop)   stop ;;
  status) status ;;
  start_app) start_app ;;
  *) echo "用法: sudo $0 {setup|start|stop|status}"; exit 1 ;;
esac
