from playwright.async_api import async_playwright
import asyncio


if __name__ == "__main__":
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webManager.utils.baseImageCreator import BaseImageCreator
from webManager.utils.helper import read_yaml




class BaseWhetherReport(BaseImageCreator):
    def __init__(self,config):
        self.config=config

    def when_config_change(self):
        pass

    async def create_image(self):
        base_url = f"http://0.0.0.0:{self.config['basic_port']}/whether"

        image=await self.url_to_image(base_url)
        return image




if __name__ == "__main__":
    asyncio.run(BaseWhetherReport(config=read_yaml("webManager/config/basic.yaml")).create_image())