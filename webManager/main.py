


from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from utils.helper import read_yaml
from router import page,apis
import uvicorn

if __name__ == "__main__":
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webManager.utils.baseImageManager import BaseImageManager
from webManager.utils.baseImageSelector import BaseImageSelector

class AppServer:
    def __init__(self, config_path):

        
        self.config=read_yaml(config_path)
        self.templates = Jinja2Templates(directory="webManager/template")

       
        self.app = FastAPI()
        
        self.app.mount("/static", StaticFiles(directory="webManager/static"), name="static")

        
        self.setup_routes()

        


        @self.app.on_event("startup")
        async def start_worker():
            print("start_worker")
            self.baseImageManager=BaseImageManager(self.config)
            self.baseImageSelector=BaseImageSelector(self.config,self.baseImageManager)
            await self.baseImageManager.start_task_worker()

        
        
        # for r in self.app.router.routes:
        #     print(f"[ROUTE] {r.path} → {getattr(r, 'methods', '')}")


        
    

    def setup_routes(self):
        # home 需要 templates 和 handler → 用工厂函数
        self.app.include_router(page.get_router(self))
        # 其余 routine 直接包含
        self.app.include_router(apis.get_router(self))


    def run(self, host: str = "0.0.0.0", port: int = 8000):
        uvicorn.run(self.app, host=host, port=port)  # reload 方便开发

# ▶ 运行：
if __name__ == "__main__":
    AppServer(config_path="webManager/config/basic.yaml").run(port=23433)


