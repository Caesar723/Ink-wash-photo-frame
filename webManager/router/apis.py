from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

import numpy as np

from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse,Response,FileResponse



if TYPE_CHECKING:
    from main import AppServer


def get_router(appServer:"AppServer") -> APIRouter:
    router = APIRouter(prefix="/api")

    

    @router.post("/getconfig")
    async def getconfig(request: Request):
        pass


    @router.post("/getfolderpaths")
    async def getconfig_folderpaths(request: Request):
        pass




    
    @router.post("/evalimage")
    async def evalimage(file: UploadFile = File(...)):
        file_content = await file.read()

        
        np_array = np.frombuffer(file_content, np.uint8)

        
       


   

    return router