

import asyncio
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import uvicorn

if __name__ == "__main__":
    import sys,os
    libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
    print(libdir)
    if os.path.exists(libdir):
        print("libdir exists")
        sys.path.append(libdir)
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wifiManager.router import page,apis
from utils.helper import run_cmd


class AppServer:
    def __init__(self):

        
        
        self.templates = Jinja2Templates(directory="wifiManager/template")

       
        self.app = FastAPI()
        self.scheduler = AsyncIOScheduler()
        self.scan_results = os.getenv("WIFI_SCAN_RESULTS", "")
        
        self.app.mount("/static", StaticFiles(directory="wifiManager/static"), name="static")

        
        self.setup_routes()

        self.wifi_connect_counter = 0
        self.wifi_reconnect_counter = 0

        

        

        @self.app.on_event("startup")
        async def start_worker():
            self.scheduler.add_job(self.check_wifi_connect, "interval", seconds=5)
            self.scheduler.start()
            
        
        
        # for r in self.app.router.routes:
        #     print(f"[ROUTE] {r.path} → {getattr(r, 'methods', '')}")

        
    async def update_ssids(self):
        code, out, err = await run_cmd("nmcli -t -f CHAN,SIGNAL,SSID dev wifi")
        print(code,out,err)
        if code==0:
            self.scan_results = out
        

    async def check_wifi_connect(self):
        code, out, err = await run_cmd("nmcli", "-t", "-g", "GENERAL.STATE", "device", "show", "wlan0")
        print(code,out,err)
        if code==0:
            status = out
            self.wifi_reconnect_counter=0
            await self.update_ssids()
            if status == "100 (connected)":
                print("wifi connected")
            else:
                self.wifi_connect_counter += 1
                print("wifi disconnected")
                if self.wifi_connect_counter > 10:
                    print("wifi disconnected for 3 times, restart wifi")
                    code, out, err = await run_cmd("sudo", "bash", "/home/xuanpeichen/Desktop/Ink-wash-photo-frame/captive_open.sh", "start")
                    print(out)
                    self.wifi_connect_counter = 0
        else:
            self.wifi_reconnect_counter+=1
            if self.wifi_reconnect_counter > 10:
                self.wifi_reconnect_counter = 0
                print("wifi reconnect for 3 times, restart wifi")
                await run_cmd("sudo", "bash", "/home/xuanpeichen/Desktop/Ink-wash-photo-frame/captive_open.sh", "stop")

                await asyncio.sleep(5)
                
                code, out, err = await run_cmd("nmcli", "-t", "-g", "GENERAL.STATE", "device", "show", "wlan0")
                print(code, out, err)
                if code !=0 or out!= "100 (connected)":
                    print("wifi reconnect failed when restart wifi, restart wifi")
                    code, out, err = await run_cmd("sudo", "bash", "/home/xuanpeichen/Desktop/Ink-wash-photo-frame/captive_open.sh", "start")
                    
                    
                
            

    def setup_routes(self):
        # home 需要 templates 和 handler → 用工厂函数
        self.app.include_router(page.get_router(self))
        # 其余 routine 直接包含
        self.app.include_router(apis.get_router(self))


    def run(self, host: str = "0.0.0.0", port: int = 80):
        uvicorn.run(self.app, 
        host=host, 
        port=port,
        )  # reload 方便开发

# ▶ 运行：
if __name__ == "__main__":
    AppServer().run()


