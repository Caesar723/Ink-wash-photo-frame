from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
from openai import AsyncOpenAI
import random
from playwright.async_api import async_playwright
from io import BytesIO
import httpx
import asyncio
from datetime import datetime


from webManager.utils.baseHookManager import BaseHookManager

class BaseImageCreator(BaseHookManager):
    def __init__(self,config):
        super().__init__()
        self.config=config

        self.client = AsyncOpenAI(
            api_key=self.config["chat_api_token"],  
            base_url=self.config["chat_base_url"],
            
        )
        
    async def get_chat_response(self,extra=None):
        
        message=self.get_chat_prompt(extra)
        print(message)
        response = await self.client.chat.completions.create(
            model=self.config["chat_model"],
            messages=message,
            temperature=1.0,
        )
        content=response.choices[0].message.content
        print(content)
        
        return content

    def when_config_change(self,key,value):
        pass

    async def create_image(self):
        pass

    def get_image_path(self,base_path):
        image_paths=os.listdir(base_path)
        path=random.choice(image_paths)
        return path

    def image_preprocess(self,image):
        # 原始尺寸
        original_width, original_height = image.size
        target_width, target_height = self.config["target_img_size"]

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
        #print(self)
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={"width": self.config["target_img_size"][0], "height": self.config["target_img_size"][1]},
                device_scale_factor=1,
            )
            #print({"width": self.config["target_img_size"][0], "height": self.config["target_img_size"][1]})
            page = await context.new_page()
            
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(1000)
            image_bytes = await page.screenshot()
            await browser.close()

            image = Image.open(BytesIO(image_bytes))

        #image.show()
        return image

    def image_final_process(self,image):
        pass



    async def fetch_weather_and_forecast_async(self, timeout: float = 10.0):

        api_key=self.config["whether_api_token"]
        city_name=self.config["whether_city"]
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



