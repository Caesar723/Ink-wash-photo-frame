
import random




from apscheduler.schedulers.asyncio import AsyncIOScheduler

from webManager.utils.helper import get_class_by_name
from webManager.utils.baseImageManager import BaseImageManager
from webManager.utils.baseHookManager import BaseHookManager


class BaseImageSelector(BaseHookManager):
    def __init__(self,config,baseImageManager:BaseImageManager):
        super().__init__()
        self.config=config
        self.baseImageManager=baseImageManager
        self.modules=[
            get_class_by_name(class_name)(self.config)
            for class_name in self.config["module_used"]
        ]
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

        

    def when_config_change(self,key,value):
        pass

    

    async def select_image(self):
        module = random.choice(self.modules)
        image = await module.create_image()  # Await the async function

        await self.baseImageManager.put_image_to_screen(image)
        

    def start(self):
        self.scheduler.add_job(self.select_image, 'interval', 
        minutes=self.config["image_selector_interval"]["minutes"],
        hours=self.config["image_selector_interval"]["hours"],
        days=self.config["image_selector_interval"]["days"])

        # Add job that runs every 1 hour
        # self.scheduler.add_job(self.select_image, 'interval', hours=1)

        # # Add job that runs every 1 day
        # self.scheduler.add_job(self.select_image, 'interval', days=1)

        self.scheduler.start()


    def change_job(self):
        pass