from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

import numpy as np

from fastapi import UploadFile, File,HTTPException,Form
from fastapi.responses import StreamingResponse,Response,FileResponse

from utils.helper import run_cmd, get_wifi_iface

if TYPE_CHECKING:
    from main import AppServer


def get_router(appServer:"AppServer") -> APIRouter:
    router = APIRouter(prefix="/api")


    

    @router.get("/ssids")
    async def get_ssids(request: Request):
        print("client:", request.client.host)
        iface = await get_wifi_iface()

        # trigger a rescan (non-blocking in NM; listing below will read latest cache)
        await run_cmd("nmcli", "dev", "wifi", "rescan", "ifname", iface)

        code, out, err = await run_cmd("nmcli", "-t", "-f", "SSID", "dev", "wifi", "list", "ifname", iface)
        if code != 0:
            raise HTTPException(status_code=500, detail=f"nmcli error: {err or 'failed to list ssids'}")

        # Clean, de-dup, keep order
        raw = [s.strip() for s in out.splitlines() if s.strip()]
        seen, ordered = set(), []
        for s in raw:
            if s not in seen:
                ordered.append(s)
                seen.add(s)

        return {"ssids": ordered}


    @router.post("/connect")
    async def connect(request: Request, ssid: str = Form(...), psk: str = Form(default="")):
        print("client:", request.client.host)
        iface = await get_wifi_iface()

        # Try connecting. If psk为空，nmcli 会尝试以开放网络连接
        cmd = ["nmcli", "dev", "wifi", "connect", ssid, "ifname", iface]
        if psk:
            cmd += ["password", psk]

        code, out, err = await run_cmd(*cmd)
        if code != 0:
            # 有时需要先删除旧连接再连一次
            # 取消注释以下两行可在失败时重试（谨慎使用）：
            # await run_cmd("nmcli", "connection", "delete", ssid)
            # code, out, err = await run_cmd(*cmd)

            return {"ok": False, "message": err or out or "connect failed"}

        return {"ok": True, "message": out or "connected"}


    @router.get("/status")
    async def status(request: Request):
        print("client:", request.client.host)
        iface = await get_wifi_iface()

        code, out, err = await run_cmd("nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "dev", "status")
        if code != 0:
            raise HTTPException(status_code=500, detail=f"nmcli error: {err or 'failed to read status'}")

        connected = False
        ssid = None
        for line in out.splitlines():
            # e.g., wlan0:connected:MyWiFi
            parts = line.split(":")
            if len(parts) >= 3 and parts[0] == iface and parts[1] == "connected":
                connected = True
                ssid = parts[2] or None
                break

        ip = None
        if connected:
            # Get IPv4 address for iface (format: 192.168.1.23/24)
            code, ipout, _ = await run_cmd("nmcli", "-g", "IP4.ADDRESS", "device", "show", iface)
            if ipout:
                first = ipout.splitlines()[0]
                ip = (first.split("/", 1)[0] or None)
            if not ip:
                # Fallback: first non-loopback address from hostname -I
                code, ipout, _ = await run_cmd("hostname", "-I")
                if ipout:
                    ip = next((tok for tok in ipout.split() if not tok.startswith("127.")), None)

        # 符合你前端对 d.connected && d.ip 的判断
        return {
            "connected": connected,
            "ip": ip,
            "ssid": ssid,
            "iface": iface,
        }
    return router

    