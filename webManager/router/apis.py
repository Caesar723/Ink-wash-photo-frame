from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

import numpy as np

from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse,Response,FileResponse



if TYPE_CHECKING:
    from main import AppServer


def get_router(appServer:"AppServer") -> APIRouter:
    router = APIRouter(prefix="/api")

    


    @router.post("/get_img_index")
    async def get_img_index(request: Request):
        pass




    
    @router.post("/use_image")
    async def use_image(request: Request):
        pass 
       

    @router.post("/change_place_mode")
    async def change_place_mode(request: Request):
        pass 
       

    @router.post("/set_time_gap")
    async def set_time_gap(request: Request):
        pass 



    @router.post("/set_module_list")
    async def set_module_list(request: Request):
        pass
       

   

    return router