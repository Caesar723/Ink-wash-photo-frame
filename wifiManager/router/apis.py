from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

import numpy as np

from fastapi import UploadFile, File,HTTPException
from fastapi.responses import StreamingResponse,Response,FileResponse



if TYPE_CHECKING:
    from main import AppServer


def get_router(appServer:"AppServer") -> APIRouter:
    router = APIRouter(prefix="/api")


    

    @router.post("/uploadImage")
    async def uploadImage(file: UploadFile = File(..., alias="filepond")):
        pass

    return router
   