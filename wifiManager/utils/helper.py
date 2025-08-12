import asyncio



def parse_scan_results(scan_results: str):
    """
    处理 scan_results 字符串：
    1. 只保留信道 <= 14 的
    2. 信号强度从大到小排序
    3. 排除空白 SSID
    """
    entries = []
    for line in scan_results.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 3:
            continue
        try:
            chan = int(parts[0])       # 信道
            signal = int(parts[1])     # 信号强度
        except ValueError:
            continue
        ssid = parts[2].strip()
        if chan <= 14 and ssid:  # 条件：信道小于等于 14 且 SSID 非空
            entries.append((signal, ssid))

    # 按信号强度从大到小排序
    entries.sort(key=lambda x: x[0], reverse=True)

    # 返回排序后的 SSID 列表
    return [ssid for _, ssid in entries]
async def run_cmd(*args: str) -> tuple[int, str, str]:
    """Run a command asynchronously and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    return proc.returncode, out.decode().strip(), err.decode().strip()

async def get_wifi_iface() -> str:
    """Detect the Wi-Fi interface name (e.g., wlan0)."""
    code, out, err = await run_cmd("nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "dev", "status")
    if code != 0:
        # Fallback commonly used on Raspberry Pi
        return "wlan0"
    for line in out.splitlines():
        # Format: wlan0:wifi:connected
        parts = line.split(":")
        if len(parts) >= 2 and parts[1] == "wifi":
            return parts[0]
    return "wlan0"