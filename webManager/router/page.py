

from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

import numpy as np

from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse,Response,FileResponse
from fastapi.templating import Jinja2Templates


if TYPE_CHECKING:
    from webManager.main import AppServer








def get_router(appServer:"AppServer") -> APIRouter:
    router = APIRouter()
    

    
    @router.get("/whether")
    async def whether(request: Request):
        city = appServer.config["whether_city"]
        api_key = appServer.config["whether_api_token"]
        print(city,api_key)

        return appServer.templates.TemplateResponse(
            "whether.html", 
            {
            "request": request,
            "city_name": city,
            "api_key": api_key,
            }
        )

    @router.get("/text")
    async def text(request: Request):
        return appServer.templates.TemplateResponse(
            "textContainer.html", 
            {
            "request": request,
            }
        )


    @router.get("/")
    async def index(request: Request):
        print("index")
        return FileResponse("webManager/template/home.html")




   

    return router