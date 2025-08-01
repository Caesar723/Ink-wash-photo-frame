from openai import AsyncOpenAI
import asyncio
import random
from PIL import Image
from io import BytesIO
from playwright.async_api import async_playwright
from datetime import datetime
from urllib.parse import urlencode
import math
from typing import List
import os

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from webManager.utils.helper import read_yaml
from webManager.utils.baseImageCreator import BaseImageCreator

class ThreeCombineOne(BaseImageCreator):
    def __init__(self,config):
        super().__init__(config)
        
    async def get_whether_data(self):
        pass

    def get_chat_prompt(self,summary_whether=None):
        themes = ["晴日","微风","雨夜","斜阳","光影","静谧","流光","时光","回忆","远行",
          "温暖","思念","清晨","黄昏","星辰","梦境","海浪","岁月","柔情","烟雨",
          "雪落","暖阳","寒意","寂寞","安然","低语","心境","触感","余晖","山川",
          "归途","浅笑","轻语","幽光","朦胧","远望","听雨","怀旧","细腻","旷野",
          "惊喜","渐变","归属","奏鸣","纯净","悠然","释怀","回声","旅途","花影"]

        themes=random.choice(themes)
        prompt=rf'''
你是中文诗意文案生成器。请每次生成一句新的、优雅细腻、有画面感的中文短句,主题是{themes}，描绘某种天气下的感官与心境：比如阳光、微风、云影、清爽、光与影交织、时间被雕琢成艺术、静谧与珍惜等。不要照搬原句“在这样的天气里，保持清爽，感受日光与微风交织出的静谧，让每一刻都像被精心雕琢的画面。”中的固定搭配，要有明显变体和随机性。要求如下：

1. 仅输出一句话，不要多余说明。  
2. 自然融合天气元素与内心/感官体验，营造出清新、沉静、珍惜当下、如艺术品般精致的氛围。  
3. 文字风格高雅、有节奏感，可适度用修辞（比喻、铺陈、对偶等），但不过度浮夸。  
4. 句中汉字数量控制在大约 34 到 42 个之间（标点不计入）。  
5. 每次生成要尽可能随机：天气类型、意象、词汇、结构都应变化，避免重复前几次的表达。  
6. 只用中文，不使用英文、数字或表情符号。  

示例（仅供参考，不要照搬）：“微风在枝叶间低语，斜阳撒下柔和纹理，静默时光宛如细细打磨的画卷缓缓展开。”
 
        '''
        #summary_whether=dict(summary_whether)

        condition=summary_whether["condition"]
        messages=[
            {"role": "system",  "content": prompt},
            {"role": "user",  "content": f"现在的天气是{condition}，帮我写一个短句「{themes}」的诗意文案"},
        ]

        return messages

    async def get_chat_response(self):
        
        data=await self.fetch_weather_and_forecast_async()
        summary=self.summarize_weather(data,12)
        
        content=await super().get_chat_response(summary)
        
        
            
        return content,summary

    def when_config_change(self):
        pass

    async def create_image(self):
        base_url = f"http://0.0.0.0:{self.config['basic_port']}/threeCombineOne"
        content,summary_whether=await self.get_chat_response()
        #font_path=self.get_font_path()

        img_path=self.get_image_path(self.config["basic_store_path"])
        
        params = {
            "text": content,
            "temp":summary_whether["current_temp"],
            "condition":summary_whether["condition"],
            "max_temp":summary_whether["max_temp"],
            "min_temp":summary_whether["min_temp"],
            "img_path":f"static/images/shored_img/{img_path}",
            #"font": font_path
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


    def classify_weather(self,main: str, description: str) -> str:
        """
        只输出四种：sunny, rain, cloudy, snow, clear
        """
        m = (main or "").lower()
        d = (description or "").lower()

        if m == "clear":
            return "clear"
        if m == "snow":
            return "snow"
        if m in ("rain", "drizzle", "thunderstorm"):
            return "rain"
        if m == "clouds":
            return "cloudy"

        # fallback based on description keywords
        if "snow" in d:
            return "snow"
        if any(k in d for k in ("rain", "shower", "storm", "drizzle", "thunder")):
            return "rain"
        if "clear" in d:
            return "sunny"
        if any(k in d for k in ("cloud", "mist", "fog", "haze", "smoke", "dust")):
            return "cloudy"

        # 默认归类为 cloudy（比 sunny 更保守）
        return "cloudy"

    def extract_precipitation(self,slot) -> float:
        """
        返回该时间段的降水量（mm），优先 rain 再 snow，取 '3h' 字段，如果都没有则 0。
        """
        vol = 0.0
        if "rain" in slot and isinstance(slot["rain"], dict):
            vol = slot["rain"].get("3h", 0.0)
        elif "snow" in slot and isinstance(slot["snow"], dict):
            vol = slot["snow"].get("3h", 0.0)
        return vol


    def summarize_weather(self,data: dict, upcoming_hours: int = 12) -> dict:
        """
        输入 fetch_weather_and_forecast_async 返回的 data，提取所需 summary。
        upcoming_hours 是要看未来多少小时（默认 12h，3h 一个 slot）。
        """
        current = data["current"]
        forecast_list = data["forecast"]["list"]  # 3h 间隔

        # 当前温度 / 体感 / weather info

        today=datetime.now().strftime("%Y-%m-%d")

        forecast_list=[forecast for forecast in forecast_list if forecast["dt_txt"].startswith(today)]

        min_temps=[forecast["main"]["temp_min"] for forecast in forecast_list]
        max_temps=[forecast["main"]["temp_max"] for forecast in forecast_list]
        
        current_temp = current.get("main", {}).get("temp")

        min_temps.append(current_temp)
        max_temps.append(current_temp)
        max_temp = max(max_temps)
        min_temp = min(min_temps)
        feels_like = current.get("main", {}).get("feels_like")
        weather_info = current.get("weather", [{}])[0]
        main_desc = weather_info.get("main", "")
        detail_desc = weather_info.get("description", "")
        condition = self.classify_weather(main_desc, detail_desc)

        # 计算需要取几个 forecast slot（向上取整）
        slots_needed = math.ceil(upcoming_hours / 3)
        upcoming: List[dict] = []
        for slot in forecast_list[:slots_needed]:
            dt_txt = slot.get("dt_txt")  # 例如 "2025-07-31 18:00:00"
            temp = slot.get("main", {}).get("temp")
            pop = slot.get("pop", 0.0)  # precipitation probability 0..1
            precip_mm = self.extract_precipitation(slot)
            slot_weather = slot.get("weather", [{}])[0]
            slot_main = slot_weather.get("main", "")
            slot_desc = slot_weather.get("description", "")
            slot_condition = self.classify_weather(slot_main, slot_desc)

            upcoming.append({
                "time": dt_txt,
                "temp": temp,
                "condition": slot_condition,
                "description": slot_desc,
                "precipitation_mm": precip_mm,
                "precipitation_chance_pct": round(pop * 100),  # 百分比
            })

        

        summary = {
            "city": data["city"],
            "max_temp": max_temp,
            "min_temp": min_temp,
            "current_temp": current_temp,
            "feels_like": feels_like,
            "condition": condition,
            "description": detail_desc,
            "upcoming": upcoming
        }
        return summary







if __name__ == "__main__":
    async def main():
        print(sys.path)
        config=read_yaml("webManager/config/basic.yaml")
        image_reader=ThreeCombineOne(config)
        
        image=await image_reader.create_image()
        image.show()
        

        

    asyncio.run(main())