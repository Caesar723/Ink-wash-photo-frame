from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import os
from openai import AsyncOpenAI
import random
from playwright.async_api import async_playwright
from io import BytesIO
import httpx
import asyncio
from datetime import datetime
import numpy as np
import cv2
import math
import mediapipe as mp

from webManager.utils.helper import region_metrics,face_boxes_from_image,region_metrics_3x3
from webManager.utils.baseHookManager import BaseHookManager
from webManager.utils.baseBrowserRenderer import BrowserRenderer

class BaseImageCreator(BaseHookManager):
    browser_renderer = None

    def __init__(self,config):
        super().__init__()
        self.config=config

        self.client = AsyncOpenAI(
            api_key=self.config["chat_api_token"],  
            base_url=self.config["chat_base_url"],
            
        )
        
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
        
        if BaseImageCreator.browser_renderer is None:
            BaseImageCreator.browser_renderer = BrowserRenderer(config)
        
    async def get_chat_response(self,extra=None):
        
        message=self.get_chat_prompt(extra)
        
        response = await self.client.chat.completions.create(
            model=self.config["chat_model"],
            messages=message,
            temperature=1.0,
            timeout=90.0,
        )
        content=response.choices[0].message.content
        
        
        return content

    def when_config_change(self,key,value):
        pass


    async def create_image_whole_process(self):
        image=await self.create_image()
        image=self.image_final_process(image)
        return image

    async def create_image(self):
        pass

            


    def get_image_path(self,base_path):
        image_paths=os.listdir(base_path)
        
        max_attempts=3
        tolerance=0.5
        expected_ratio=self.config["target_img_size"][0]/self.config["target_img_size"][1]
        print(expected_ratio)
        
        for _ in range(max_attempts):
            path = random.choice(image_paths)
            full_path = os.path.join(base_path, path)

            try:
                with Image.open(full_path) as img:
                    img=ImageOps.exif_transpose(img)
                    width, height = img.size
                    
                    ratio = width / height
                    print(ratio)
                    
                    if abs(ratio - expected_ratio) <= tolerance:
                        return path
            except Exception as e:
                print(f"跳过无效图片: {full_path}，错误: {e}")
                continue
        return path

    def image_preprocess(self,image):
        #image.show()
        
        # 原始尺寸
        original_width, original_height = image.size
        target_width, target_height = self.config["target_img_size"][1],self.config["target_img_size"][0]

        # 缩放比例（保持宽高比）
        ratio = min(target_width / original_width, target_height / original_height)
        new_size = (int(original_width * ratio), int(original_height * ratio))

        # 缩放
        resized_img = image.resize(new_size, Image.LANCZOS)

        # 居中扩张
        delta_w = target_width - new_size[0]
        delta_h = target_height - new_size[1]
        padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)

        # 扩张到目标大小
        
        image = ImageOps.expand(resized_img, padding, fill=(0, 0, 0))
        return image


    def _read_pil(self,image_path):
        
        if not os.path.exists(image_path):
            return Image.new("RGB", self.config["target_img_size"], (255, 255, 255))
        img = Image.open(image_path)
        img=ImageOps.exif_transpose(img)
        img=self.image_preprocess(img)
        return img


    async def url_to_image(self,url: str):
        return await BaseImageCreator.browser_renderer.render_url(url)

    def image_rotate(self,image):
        if self.config["target_img_size"][0]>self.config["target_img_size"][1]:
            
            image= image.rotate(-90, expand=True)
        else:
            
            image= image.rotate(180, expand=True)
        return image

    def image_final_process(self,image):
        saturation_factor = 2  # 提高饱和度 50%
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation_factor)
        
        
        image=self.image_rotate(image)
        
        #(800,480)
        image=self.image_resize(image)
        
        return image

    def image_resize(self,image):
        
        background=np.zeros((480,800,3), dtype=np.uint8)
        idx_x=self.config["resize_offset"][0]
        idx_x_end=idx_x+self.config["resize_image_size"][0]
        idx_y=self.config["resize_offset"][1]
        idx_y_end=idx_y+self.config["resize_image_size"][1]
        
        background[idx_x:idx_x_end,idx_y:idx_y_end]=image
        background=Image.fromarray(background)
        
        return background



    async def fetch_weather_and_forecast_async(self, timeout: float = 10.0):

        api_key=self.config["whether_api_token"]
        city_name=self.config["whether_city"]

        timeout = httpx.Timeout(90.0) 
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 1. 地理编码
            geo_resp = await client.get(
                "https://api.openweathermap.org/geo/1.0/direct",
                params={"q": city_name, "limit": 1, "appid": api_key}
            )
            geo_resp.raise_for_status()
            loc = geo_resp.json()
            if not loc:
                raise ValueError("未找到城市")
            loc0 = loc[0]
            lat = loc0["lat"]
            lon = loc0["lon"]
            resolved_name = loc0.get("name", city_name)

            # 2. 并发获取当前天气和预报
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
            tasks = [
                client.get(weather_url, params={
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "appid": api_key
                }),
                client.get(forecast_url, params={
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "appid": api_key
                }),
            ]
            weather_resp, forecast_resp = await asyncio.gather(*tasks)
            weather_resp.raise_for_status()
            forecast_resp.raise_for_status()
            current = weather_resp.json()
            forecast = forecast_resp.json()

            date_str = self.format_date(datetime.now())

            return {
                "city": resolved_name,
                "date": date_str,
                "current": current,
                "forecast": forecast,
            }

    def format_date(self,dt: datetime) -> str:
        WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        MONTHS = ["一月", "二月", "三月", "四月", "五月", "六月",
                "七月", "八月", "九月", "十月", "十一月", "十二月"]
        return f"{WEEKDAYS[dt.weekday()]} {MONTHS[dt.month-1]} {dt.day}"



    def face_detection(self,image):
        image=np.array(image)[:,:,:3]
        boxes = face_boxes_from_image(image, model_selection=1, min_conf=0.6)
        return boxes


    def image_crop(self,image, mode: str = "center", upscale: bool = True):

        target_height, target_width = self.config["target_img_size"]
        original_width, original_height = image.size

        # 为兼容 Pillow 新旧版本的 LANCZOS
        Resampling = getattr(Image, "Resampling", Image)
        resample = Resampling.LANCZOS

        # 缩放比例：为覆盖目标，用 max（让短边也能到达目标）
        scale = max(target_width / original_width, target_height / original_height)

        if not upscale:
            # 不允许放大时，最多保持 1.0；如果仍不足以覆盖，后续会报错或可选择改为填充
            scale = min(1.0, scale)

        new_w = max(1, int(math.ceil(original_width * scale)))
        new_h = max(1, int(math.ceil(original_height * scale)))

        resized = image.resize((new_w, new_h), resample=resample)

        
        if new_w < target_width or new_h < target_height:
            return ImageOps.pad(image, (target_width, target_height), method=resample, color=(0,0,0), centering=(0.5,0.5))

        # 计算裁剪起点（根据对齐方式）
        def get_offsets(mode_str: str):
            # 水平
            if "left" in mode_str:
                left = 0
            elif "right" in mode_str:
                left = new_w - target_width
            else:  # center / top / bottom
                left = (new_w - target_width) // 2

            # 垂直
            if "top" in mode_str:
                top = 0
            elif "bottom" in mode_str:
                top = new_h - target_height
            else:  # center / left / right
                top = (new_h - target_height) // 2

            # 边界保护
            left = max(0, min(left, new_w - target_width))
            top = max(0, min(top, new_h - target_height))
            return left, top

        left, top = get_offsets(mode.lower())
        box = (left, top, left + target_width, top + target_height)
        out = resized.crop(box)
        print(out.size)
        
        return out

    def get_area_index(self):
        return {
            "left_bottom":[0,7,11,14],
            "right_bottom":[7,13,16],
            "left_top":[4,14],
            "right_top":[2,13],
            "left_mid":[5,8,9,14,17,19],
            "right_mid":[8,13,16,17,19],
            "mid_top":[4],
            "mid_bottom":[10,16,18],
            "mid_mid":[1,6,8,9,12,15,16,17,19],
            "free":[0,2,3,7,10,11]#如果都不行就用万能的
        }

    def get_fit_area(self,image):
        image=self.image_crop(image)
        boxes=self.face_detection(image)
        image=cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        _,_, areas=region_metrics_3x3(np.array(image)[:,:,:3],boxes=boxes,box_policy="iou",iou_thr=0.05)

        union_free_area=set(range(20))
        nonfree_areas=areas[3:]
        area_indexs=self.get_area_index()
 
        union_nonfree_area=set()

        for area in nonfree_areas:
            union_nonfree_area=union_nonfree_area.union(set(area_indexs[area]))
        #print(union_nonfree_area)
        except_area=union_free_area.intersection(union_nonfree_area)
        #print(except_area)
        result_area=union_free_area-except_area
        print(result_area)
        if len(result_area)==0:
            print("没有找到合适的区域")
            return area_indexs["free"]
        return result_area



    def smart_face_crop(self,image, edge_thresh_ratio=0.12, face_pick="largest"):
        """
        根据人脸在画面中的位置自动选择裁剪模式：
        - 人脸靠边：用 left/right/top/bottom
        - 正常：用 center

        Params
        ------
        image: PIL.Image 或 numpy 数组，能被 poster.face_detection 处理
        poster: 你已有的对象，需提供
            - poster.face_detection(image) -> List[[x1,y1,x2,y2], ...]  像素坐标
            - poster.image_crop(image, mode="center")                 执行裁剪
        edge_thresh_ratio: float
            判定“靠边”的阈值，占图像宽/高的比例。比如 0.12 表示边缘 12% 宽度/高度的区域。
        face_pick: "largest" | "nearest_center"
            多人脸时如何挑选：最大框 或 最靠近中心的框
        """
        # 1) 获取图像尺寸
        if hasattr(image, "shape"):  # numpy
            H, W = image.shape[:2]
        else:
            W, H = image.size  # PIL

        # 2) 检测人脸框
        boxes = self.face_detection(image) or []
        

        # 若无脸，直接居中裁剪
        if not boxes:
            return self.image_crop(image, mode="center")

        # 3) 选择一个“主脸”
        def box_area(b):
            x1, y1, x2, y2 = b
            return max(0, x2 - x1) * max(0, y2 - y1)

        def box_center_dist2(b):
            x1, y1, x2, y2 = b
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            dx, dy = cx - W / 2.0, cy - H / 2.0
            return dx * dx + dy * dy

        if len(boxes) > 1:
            if face_pick == "largest":
                face = max(boxes, key=box_area)
            else:
                face = min(boxes, key=box_center_dist2)
        else:
            face = boxes[0]

        x1, y1, x2, y2 = face
        # 人脸中心与边缘距离（像素）
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        dist_left   = cx - 0
        dist_right  = W - cx
        dist_top    = cy - 0
        dist_bottom = H - cy

        # 4) 计算“靠边阈值”（像素）
        thr_w = W * edge_thresh_ratio
        thr_h = H * edge_thresh_ratio

        # 5) 判断靠哪条边
        # 优先级：谁更近用谁；如果左右都近，选更近的那一侧；上下同理。
        # 若四个方向都大于阈值 → center
        choices = []
        if dist_left   < thr_w: choices.append(("left",   dist_left))
        if dist_right  < thr_w: choices.append(("right",  dist_right))
        if dist_top    < thr_h: choices.append(("top",    dist_top))
        if dist_bottom < thr_h: choices.append(("bottom", dist_bottom))

        if not choices:
            mode = "center"
        else:
            # 选距离最小的边
            mode = min(choices, key=lambda x: x[1])[0]
        
        return self.image_crop(image, mode=mode)