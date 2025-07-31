from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

import numpy as np

from fastapi import UploadFile, File,HTTPException
from fastapi.responses import StreamingResponse,Response,FileResponse

import aiofiles
import aiofiles.os as aos
import os
import uuid
from PIL import Image


if TYPE_CHECKING:
    from main import AppServer

from webManager.utils.helper import get_class_by_name

def get_router(appServer:"AppServer") -> APIRouter:
    router = APIRouter(prefix="/api")


    ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ALLOWED_MIMES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    }
    UPLOAD_DIR = "webManager/static/images/shored_img"

    # 简单的文件头嗅探，防止伪装（可按需扩展）
    def sniff_image_type(header: bytes) -> "str | None":
        if header.startswith(b"\xFF\xD8\xFF"):
            return ".jpg"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return ".png"
        if header[:6] in (b"GIF87a", b"GIF89a"):
            return ".gif"
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return ".webp"
        return None

    @router.post("/uploadImage")
    async def uploadImage(file: UploadFile = File(..., alias="filepond")):
        # 1) 基础校验：MIME
        if file.content_type not in ALLOWED_MIMES:
            raise HTTPException(status_code=400, detail="不支持的图片类型（MIME）")

        # 2) 嗅探前 32B 文件头，核实真实类型
        header = await file.read(32)
        ext_by_sniff = sniff_image_type(header)
        if ext_by_sniff is None:
            raise HTTPException(status_code=400, detail="无法识别的或不被允许的图片格式")
        # 回到文件开头，准备异步流式写入
        await file.seek(0)

        # 3) 限制大小（例如 10MB）
        MAX_BYTES = 10 * 1024 * 1024
        total = 0

        # 4) 生成唯一文件名并异步保存
        file_id = f"{uuid.uuid4()}{ext_by_sniff}"
        save_path = os.path.join(UPLOAD_DIR, file_id)
        CHUNK = 1 * 1024 * 1024

        try:
            async with aiofiles.open(save_path, "wb") as f:
                while True:
                    chunk = await file.read(CHUNK)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise HTTPException(status_code=413, detail="文件过大")
                    await f.write(chunk)
        except HTTPException:
            # 清理半成品
            if os.path.exists(save_path):
                os.remove(save_path)
            raise
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            raise HTTPException(status_code=500, detail=f"保存失败: {e}")

        # 5) 返回结果（你前端的 onload 可直接解析 JSON）
        return {"id": file_id, "url": f"/static/{file_id}"}


    @router.post("/get_img_index")
    async def get_img_index(request: Request):
        index_list=os.listdir(UPLOAD_DIR)
        return {"index_list":index_list}




    
    @router.post("/use_image")
    async def use_image(request: Request):
        data=await request.json()
        index=data["index"]
        image_path=os.path.join(UPLOAD_DIR,index)
        if os.path.exists(image_path):
            image=Image.open(image_path)
            image=appServer.baseImageCreator.image_preprocess(image)
            image=appServer.baseImageCreator.image_final_process(image)
            await appServer.baseImageManager.put_image_to_screen(image)

            return {"status":"success"}
        else:
            raise HTTPException(status_code=404, detail="图片不存在")

    @router.post("/delete_image")
    async def delete_image(request: Request):
        data=await request.json()
        index=data["index"]
        image_path=os.path.join(UPLOAD_DIR,index)
        if os.path.exists(image_path):
            await aos.remove(image_path)
            return {"status":"success"}
        else:
            raise HTTPException(status_code=404, detail="图片不存在")
       

    @router.post("/change_place_mode")
    async def change_place_mode(request: Request):
        data=await request.json()
        mode=data["mode"]
        print(mode)

        if mode=="horizontal":
            appServer.config["target_img_size"]= [800, 480]
        elif mode=="vertical":
            appServer.config["target_img_size"]=[480,800]
        
        
        return {"status":"success"}
       

    @router.post("/setTime")
    async def setTime(request: Request):
        data=await request.json()
        print(data)
        days=data["days"]
        hours=data["hours"]
        minutes=data["minutes"]
        appServer.config["image_selector_interval"]={"days":days,"hours":hours,"minutes":minutes}

        appServer.baseImageSelector.scheduler.reschedule_job(
            'select_image_job',
            trigger='interval',
            days=days,
            hours=hours,
            minutes=minutes,
            # 也可以加 seconds、weeks 等
        )
        
        print(days,hours,minutes)
        return {"status":"success"}


    @router.post("/get_module_list")
    async def get_module_list(request: Request):
        module_list=appServer.config["module_used"]
        total_module_list=list(appServer.config["module_dict"].keys())
        print(module_list,total_module_list)

        return {"module_list":module_list,"total_module_list":total_module_list}


    @router.post("/set_module_list")
    async def set_module_list(request: Request):
        data=await request.json()
        module_list=data["module_list"]

        baseImageSelector=appServer.baseImageSelector

        baseImageSelector.modules=[
            baseImageSelector.total_modules[class_name]
            for class_name in module_list
        ]

        appServer.config["module_used"]=module_list
        
        
        return {"status":"success"}


    @router.post("/set_city")
    async def set_city(request: Request):
        data=await request.json()
        city=data["city"]
        print(city)
        appServer.config["whether_city"]=city
        return {"status":"success"}



    @router.post("/change_image")
    async def change_image(request: Request):
        await appServer.baseImageSelector.select_image()
        return {"status":"success"}
       

   

    return router