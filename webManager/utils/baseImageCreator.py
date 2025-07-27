from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
from openai import AsyncOpenAI
import random
from playwright.async_api import async_playwright
from io import BytesIO

from webManager.utils.baseHookManager import BaseHookManager

class BaseImageCreator(BaseHookManager):
    def __init__(self,config):
        super().__init__()
        self.config=config

        self.client = AsyncOpenAI(
            api_key=self.config["chat_api_token"],  
            base_url=self.config["chat_base_url"],
            
        )
        
    async def get_chat_response(self):
        
        message=self.get_chat_prompt()
        response = await self.client.chat.completions.create(
            model=self.config["chat_model"],
            messages=message,
            temperature=1.0,
        )
        content=response.choices[0].message.content
        
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
        img=self.image_preprocess(img)
        return img


    async def url_to_image(self,url: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={"width": self.config["target_img_size"][0], "height": self.config["target_img_size"][1]}
            )
            page = await context.new_page()
            
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(1000)
            image_bytes = await page.screenshot(full_page=True)
            await browser.close()

            image = Image.open(BytesIO(image_bytes))

        image.show()
        return image


    