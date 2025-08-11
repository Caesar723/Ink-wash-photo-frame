

from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

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
        return FileResponse("wifiManager/template/home.html")




   

    return router