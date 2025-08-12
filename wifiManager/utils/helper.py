import asyncio



def parse_scan_results(scan_results: str):
        """
        处理 scan_results 字符串，只保留左边数字<=14且右边有名字的项，返回名字列表
        """
        ssids = []
        for line in scan_results.splitlines():
            line = line.strip()
            if not line:
                continue
            # 允许分隔符为:或空格
            if ':' in line:
                parts = line.split(':', 1)
            elif '\t' in line:
                parts = line.split('\t', 1)
            elif ' ' in line:
                parts = line.split(' ', 1)
            else:
                # 可能没有分隔符，跳过
                continue
            if len(parts) != 2:
                continue
            try:
                num = int(parts[0])
            except ValueError:
                continue
            name = parts[1].strip()
            if num <= 14 and name:
                ssids.append(name)
        return ssids
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