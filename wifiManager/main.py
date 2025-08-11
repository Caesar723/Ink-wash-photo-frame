


from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


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



class AppServer:
    def __init__(self):

        
        
        self.templates = Jinja2Templates(directory="wifiManager/template")

       
        self.app = FastAPI()
        
        self.app.mount("/static", StaticFiles(directory="wifiManager/static"), name="static")

        
        self.setup_routes()

        

        

        @self.app.on_event("startup")
        async def start_worker():
            print("start_worker")
            
        
        
        # for r in self.app.router.routes:
        #     print(f"[ROUTE] {r.path} → {getattr(r, 'methods', '')}")


        
    

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


