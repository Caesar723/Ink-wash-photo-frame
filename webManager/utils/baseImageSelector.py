
import random
import asyncio



from apscheduler.schedulers.asyncio import AsyncIOScheduler

if __name__ == "__main__":
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from webManager.utils.helper import get_class_by_name
from webManager.utils.baseImageManager import BaseImageManager
from webManager.utils.baseHookManager import BaseHookManager
from webManager.utils.helper import read_yaml


class BaseImageSelector(BaseHookManager):
    def __init__(self,config,baseImageManager:BaseImageManager):
        super().__init__()
        self.config=config
        self.baseImageManager=baseImageManager
        self.total_modules={
            class_name:get_class_by_name(self.config["module_dict"][class_name])(self.config)
            for class_name in self.config["module_dict"]
        }
        self.modules=[
            self.total_modules[class_name]
            for class_name in self.config["module_used"]
        ]
        print(self.modules)
        self.scheduler = AsyncIOScheduler()
        self.start()

        

    def when_config_change(self,key,value):
        pass

    

    async def select_image(self):
        module = random.choice(self.modules)
        
        image = await module.create_image_whole_process()  # Await the async function
        
        await self.baseImageManager.put_image_to_screen(image)
        

    def start(self):
        self.scheduler.add_job(self.select_image, 'interval', 
        id='select_image_job',
        minutes=self.config["image_selector_interval"]["minutes"],
        hours=self.config["image_selector_interval"]["hours"],
        days=self.config["image_selector_interval"]["days"])

       
        self.scheduler.start()


    def change_job(self):
        pass

if __name__ == "__main__":
    config=read_yaml("webManager/config/basic.yaml")

    async def main():
        baseImageManager=BaseImageManager(config)
        baseImageSelector=BaseImageSelector(config,baseImageManager)

        while True:
            await asyncio.sleep(3600)
           

    asyncio.run(main())
    