

from fastapi import APIRouter, Request
from typing import TYPE_CHECKING
import socket
import numpy as np

from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse,Response,FileResponse
from fastapi.templating import Jinja2Templates


if TYPE_CHECKING:
    from wifiManager.main import AppServer








def get_router(appServer:"AppServer") -> APIRouter:
    router = APIRouter()
    
    @router.get("/")
    async def index(request: Request):
        print("index")
        
        hostname = socket.gethostname()
        port = appServer.webconfig["basic_port"]
        return appServer.templates.TemplateResponse("home.html", {
            "request": request,
            "hostname": hostname,
            "port": port
        })
        



    @router.get("/hotspot-detect.html")
    async def hotspot_detect(request: Request):
        print("hotspot-detect")
        return FileResponse("wifiManager/template/home.html")

   

    return router