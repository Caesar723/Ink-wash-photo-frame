


from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


import uvicorn

if __name__ == "__main__":
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webManager.utils.baseImageManager import BaseImageManager
from webManager.utils.baseImageSelector import BaseImageSelector
from webManager.utils.baseImageCreator import BaseImageCreator
from webManager.router import page,apis
from webManager.utils.helper import read_yaml


class AppServer:
    def __init__(self, config_path):

        
        self.config=read_yaml(config_path)
        self.templates = Jinja2Templates(directory="webManager/template")

       
        self.app = FastAPI()
        
        self.app.mount("/static", StaticFiles(directory="webManager/static"), name="static")

        
        self.setup_routes()

        

        @self.app.middleware("http")
        async def add_cache_headers(request, call_next):
            response = await call_next(request)
            if request.url.path.startswith("/static/images/shored_img/"):
                # 7 天：604800 秒
                #response.headers["Cache-Control"] = "public, max-age=604800"
                # 可选：更现代的折中策略（1 小时强缓存 + SWR 一天）
                response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
            return response

        @self.app.on_event("startup")
        async def start_worker():
            print("start_worker")
            self.baseImageManager=BaseImageManager(self.config)
            self.baseImageSelector=BaseImageSelector(self.config,self.baseImageManager)
            self.baseImageCreator=BaseImageCreator(self.config)
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


