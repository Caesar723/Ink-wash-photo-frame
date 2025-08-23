from fastapi import APIRouter, Request
from typing import TYPE_CHECKING

import numpy as np

from fastapi import UploadFile, File,HTTPException
from fastapi.responses import StreamingResponse,Response,FileResponse

import aiofiles
import aiofiles.os as aos
import os
import uuid
from PIL import Image,ImageOps


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
            image=ImageOps.exif_transpose(image)
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
       

    @router.post("/get_place_mode")
    async def get_place_mode(request: Request):
        mode=appServer.config["target_img_size"]
        if mode[0]<mode[1]:
            return {"mode":"horizontal"}
        else:
            return {"mode":"vertical"}

    @router.post("/change_place_mode")
    async def change_place_mode(request: Request):
        data=await request.json()
        mode=data["mode"]
        print(mode)

        current_size_1=appServer.config["target_img_size"][0]
        current_size_2=appServer.config["target_img_size"][1]

        if mode=="horizontal":
            appServer.config["target_img_size"]= [min(current_size_1,current_size_2),max(current_size_1,current_size_2)]
        elif mode=="vertical":
            appServer.config["target_img_size"]=[max(current_size_1,current_size_2),min(current_size_1,current_size_2)]
        
        
        return {"status":"success"}
       

    @router.post("/setTime")
    async def setTime(request: Request):
        data=await request.json()
        days=data["days"]
        hours=data["hours"]
        minutes=data["minutes"]
        if days==0 and hours==0 and minutes==0:
            return {"status":"failed"}
        
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

    @router.post("/chatai_info")
    async def chatai_info(request: Request):
        result={
            "chat_api_token":appServer.config["chat_api_token"],
            "chat_base_url":appServer.config["chat_base_url"],
            "chat_model":appServer.config["chat_model"]
        }
        return result

    @router.post("/set_chatai_info")
    async def set_chatai_info(request: Request):
        data=await request.json()

        async with appServer.config as config:
            config["chat_api_token"]=data["chat_api_token"]
            config["chat_base_url"]=data["chat_base_url"]
            config["chat_model"]=data["chat_model"]
        return {"status":"success"}


       
    @router.post("/set_size")
    async def set_size(request: Request):
        data=await request.json()
        if appServer.config["target_img_size"][0]>appServer.config["target_img_size"][1]:
            target_img_size=[data["weight"],data["height"]]
        else:
            target_img_size=[data["height"],data["weight"]]
        
        
        resize_offset=[data["offset_h"],data["offset_w"]]
        resize_image_size=[data["height"],data["weight"]]
        async with appServer.config as config:
            config["target_img_size"]=target_img_size
            config["resize_offset"]=resize_offset
            config["resize_image_size"]=resize_image_size
        return {"status":"success"}
   

    return router