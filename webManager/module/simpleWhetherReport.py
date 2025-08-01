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

class SimpleWhetherReport(BaseImageCreator):
    def __init__(self,config):
        super().__init__(config)
        
    async def get_whether_data(self):
        pass

    def get_chat_prompt(self,summary_whether=None):
        weather_joke_variants = [
            "押韵", "人设化", "一问一答", "比喻风格", "对话体", "冷知识风格", "反转幽默", "自嘲式幽默", "励志式冷笑话", "谐音梗（pun）",
            "童话风格", "科技风", "脱口秀风格", "网络梗混搭", "哲学式吐槽", "假设式问题", "荒诞派风格", "内心独白", "拟物风格", "古风改编",
            "天气播报体", "客服对话体", "朋友圈文案", "小红书体", "知乎体", "微博热搜语气", "程序员吐槽", "小学生作文", "自由诗", "广告词模仿",
            "情书风格", "恐怖故事", "地摊文学", "玄幻小说", "影评人语气", "电台 DJ", "玄学预言", "日记体", "导航语音", "语文阅读理解",
            "客服机器人", "表白失败", "相声风格", "段子手语气", "AI 自嘲", "新闻联播", "歌词改编", "电影台词", "小说旁白", "失败的鼓励师"
        ]
        prompt=rf'''
你是一个天气摘要助手。输入是一个包含当前天气和未来若干时段预报的 JSON 结构，格式如下：
{{
  "current_temp": 浮点,             
  "feels_like": 浮点,              # 体感温度
  "description": 字符串,           # 详细描述，如 "broken clouds"
  "upcoming": [                   # 当前时间之后的多个 3 小时预报
    {{
      "time": "YYYY-MM-DD HH:MM:SS",# 时间，注意有一些时间早于当前时间，所以最好可以忽略掉
      "temp": 浮点,
      "condition": 同上四种之一,
      "description": 字符串,
      "precipitation_mm": 浮点,            # 降水量（mm）
      "precipitation_chance_pct": 整数     # 降水概率百分比
    }},
    ...
  ]
}}

请根据这个数据生成一个**一句话的中文天气提醒/总结**，控制在大约 50 个中文字符以内（不需要写字段名），要涵盖下面要点：
1. 当前温度与体感（若体感比实际高 3℃ 以上，提示“闷热”或“注意补水”）。
2. 当前主要天气（如多云、下雨等）。
3. 接下来的关键变化：如果未来有一次或多次降雨（降水概率 ≥50% 或降水量 ≥0.2mm），明确指出大致开始时间并提醒带伞；如果气温在接下来几个时段变化明显（升高/降低 ≥2℃），提示温差。
4. 语气友好、实用，不要列出原始数值过多，尽量浓缩成自然流畅的一句话。
5. 最后加一句轻松幽默的小玩笑或冷笑话主题是{random.choice(weather_joke_variants)}，主题跟天气相关，避免重复说法。
示例输出（基于样例数据）：
“目前多云，27℃体感32℃闷热，18点起有小雨，出门记得带伞。” 
        '''
        summary_whether=dict(summary_whether)

        now = datetime.now()
        filtered_upcoming = []
        for entry in summary_whether.get("upcoming", []):
            try:
                t = datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
                if t > now:
                    filtered_upcoming.append(entry)
            except:
                continue
        summary_whether["upcoming"] = filtered_upcoming
        
        del summary_whether["condition"]
        messages=[
            {"role": "system",  "content": prompt},
            {"role": "user",  "content": f"{str(summary_whether)}"},
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
        base_url = f"http://0.0.0.0:{self.config['basic_port']}/whetherSimple"
        content,summary_whether=await self.get_chat_response()
        font_path=self.get_font_path()
        
        params = {
            "text": content,
            "city":summary_whether["city"],
            "temp":summary_whether["current_temp"],
            "condition":summary_whether["condition"],
            "feels_like":summary_whether["feels_like"],
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
        current_temp = current.get("main", {}).get("temp")
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

        print(data)

        summary = {
            "city": data["city"],
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
        image_reader=SimpleWhetherReport(config)
        
        image=await image_reader.create_image()
        image.show()
        

        

    asyncio.run(main())