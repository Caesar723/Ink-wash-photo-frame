import asyncio




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