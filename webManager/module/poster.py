from openai import AsyncOpenAI
import asyncio
import random
from PIL import Image
from io import BytesIO
from playwright.async_api import async_playwright
from datetime import datetime
from urllib.parse import urlencode
import re
import os
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from webManager.utils.helper import read_yaml
from webManager.utils.baseImageCreator import BaseImageCreator

class Poster(BaseImageCreator):
    def __init__(self,config):
        super().__init__(config)

        self.pre_content=self.config["pre_content"]
        

    def get_signature_with_date(self):
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        
        if 3 <= month <= 5:
            season = "春"
        elif 6 <= month <= 8:
            season = "夏"
        elif 9 <= month <= 11:
            season = "秋"
        else:
            season = "冬"
        
        date_str = f"{year}-{month:02d}-{day:02d}"
        return f"{date_str} · {season}"

    def get_content(self,response):
        pattern = r"-\s*Eyebrow：([^-\n]+)|-\s*Title：([^-\n]+)|-\s*Description：([^-\n]+)"
        matches = re.findall(pattern, response)

        data = {}
        keys = ["Eyebrow", "Title", "Description"]

        # 把匹配结果放进 dict
        for key, values in zip(keys, zip(*matches)):
            value = "".join(values).strip()
            if value:
                data[key] = value
        data["signature"]=self.get_signature_with_date()
        return data
    
    def get_chat_prompt(self,extra=None):
        
        themes = [
            "光影之间", "风起之时", "流水无声", "岁月如歌", "山川入梦",
            "云海星辰", "花开一瞬", "雨落心间", "远方呼唤", "时光有痕",
            "心若明月", "梦里江南", "青石小径", "烟火人间", "秋水长天",
            "微光初见", "暮色将晚", "晨曦未央", "风中纸鸢", "星河彼端",
            "月下独酌", "叶落归根", "风雪故人", "长夜将尽", "尘埃落定",
            "归途未远", "无声山谷", "镜中花影", "雨后初晴", "竹影婆娑",
            "松间明月", "花影流年", "江畔独行", "浮生若梦", "旧事新声",
            "北风长歌", "南山远望", "孤舟夜泊", "明日可期", "青云直上",
            "星火未央", "春水东流", "秋叶静美", "冬日暖阳", "夏风微醺",
            "白露为霜", "清风入怀", "长河落日", "野渡无人", "明月清辉"
        ]
        theme1=random.choice(themes)
        theme2=random.choice(themes)
        theme_final=f"{theme1} {theme2}"

        
        prompt=rf"""
请根据以下四个字段，生成一份适合海报展示的文案,主题是{theme_final}，整体风格需简洁、诗意、具有画面感：
格式为：
- Eyebrow：{{eyebrowText}}
- Title：{{titleText}}
- Description：{{descText}}


要求：
1. 结构分明，四部分依次呈现，且排版层次清晰。
2. 保持文字简练，不超过两行即可，突出意境与氛围。
3. 适合出现在海报中间或底部，能与画面形成呼应。
4. 举一个例子，不要和这个相似：
   - Eyebrow：一张图的故事
   - Title：在光里，遇见风
   - Description：把一句主张留给标题，把余温交给留白。让画面先说话，再让文字轻轻补全。
5，只需要返回文案，不需要其他内容。
        """

        messages=[
            {"role": "system",  "content": prompt},
            {"role": "user",  "content": "写一个海报文案"},
        ]

        return messages

    async def get_chat_response(self):
        try:
            content=await super().get_chat_response()
            self.config["pre_content"]=content
        except Exception as e:
            print(e)
            content=self.pre_content
        return content

    def when_config_change(self):
        pass

    async def create_image(self):
        base_url = f"http://0.0.0.0:{self.config['basic_port']}/poster"
        content=await self.get_chat_response()
        data=self.get_content(content)
        img_path=self.get_image_path(self.config["basic_store_path"])

        image=Image.open(os.path.join(self.config["basic_image_path"],img_path))
        areas=self.get_fit_area(image)
        
        params = {
            "index":random.choice(list(areas)),
            "eyebrow": data["Eyebrow"],
            "title": data["Title"],
            "desc": data["Description"],
            "signature": data["signature"],
            "img_path":f"static/images/shored_img/{img_path}",
        }
        url = f"{base_url}?{urlencode(params)}"
        image=await self.url_to_image(url)
        return image

    def get_font_path(self):
        base_path=self.config["basic_font_path"]
        web_base_path="/static/font"
        fonts_name=os.listdir(base_path)
        font_path=random.choice(fonts_name)
        return f"{web_base_path}/{font_path}"






if __name__ == "__main__":
    import cv2
    import numpy as np
    async def main():
        
        poster=Poster(config=read_yaml("webManager/config/basic.yaml"))
        
        image=await poster.create_image()
        image.show()
        
    asyncio.run(main())