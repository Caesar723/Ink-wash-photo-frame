from openai import AsyncOpenAI
import asyncio
import random
from PIL import Image
from io import BytesIO
from playwright.async_api import async_playwright
from datetime import datetime
from urllib.parse import urlencode
if __name__ == "__main__":
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from webManager.utils.helper import read_yaml
from webManager.utils.baseImageCreator import BaseImageCreator

class ChatApi(BaseImageCreator):
    def __init__(self,config):
        super().__init__(config)

        self.pre_content=self.config["pre_content"]
        

    def get_chat_prompt(self,extra=None):
        seed=random.randint(1,1000000)
        theme_words = ["孤独", "坚持", "成长", "自律", "梦想", "遗憾", "命运", "希望", "迷茫", "平凡",
        "沉默", "信念", "焦虑", "愧疚", "失败", "重生", "压力", "倔强", "等待", "伤痛"]

        theme = theme_words[seed % len(theme_words)]
        date_str=datetime.now().strftime("%Y-%m-%d")
        prompt=f"""
你是一位善于写心灵鸡汤的作家，每一次创作风格可以温柔、犀利或冷峻。
今天的主题是：{theme}。
写一段让人回味的短句（100字以内），可结合日常生活的情感与挣扎。
不要太套路，不要复制粘贴，不要套用格式。
        """

        messages=[
            {"role": "system",  "content": prompt},
            {"role": "user",  "content": "写一个心灵鸡汤"},
            {"role": "assistant",  "content": self.pre_content},
            {"role": "user",  "content": "再写一个不一样的"}
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
        base_url = f"http://0.0.0.0:{self.config['basic_port']}/text"
        content=await self.get_chat_response()
        font_path=self.get_font_path()
        styles=["ancient","modern","corner","floral"]
        params = {
            "text": content,
            "style": random.choice(styles),
            "font": font_path
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
    #print(ChatApi(config=read_yaml("webManager/config/basic.yaml")).get_font_path())
    asyncio.run(ChatApi(config=read_yaml("webManager/config/basic.yaml")).create_image())
    