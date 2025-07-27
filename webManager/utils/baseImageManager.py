import asyncio
import time
import os
import cv2
from PIL import Image
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from webManager.utils.helper import do_task,task_wrapper


class BaseImageManager:
    def __init__(self,config):
        self.config=config
        self.task_queue = asyncio.Queue()

    def when_config_change(self):
        pass

        

    def start_task_worker(self):
        asyncio.create_task(self.task_worker())


   
    async def store_image(self,image,name):
        loop = asyncio.get_running_loop()
        basic_store_path=self.config["basic_store_path"]
        time_str=time.strftime("%Y%m%d%H%M%S", time.localtime())
        store_path=os.path.join(basic_store_path,f"{name}_{time_str}.jpg")
        await loop.run_in_executor(None, cv2.imwrite, store_path, image)
        
    async def get_image(self):
        pass

    @task_wrapper
    def put_task(self,image):
        self.clear_image()
        self.show_image(image)

    async def put_image_to_screen(self,image):
        task=self.put_task(image)

        await self.clear_queue()
        
        await self.task_queue.put(task)


    def show_image(self,image):
        print("show image")
        print(image)
        time.sleep(3)

    def clear_image(self):
        print("clear image")
        
        time.sleep(3)

    async def clear_queue(self):
        while not self.task_queue.empty():
            await self.task_queue.get()

    async def task_worker(self):
        while True:
            task_data = await self.task_queue.get()
            
            try:
                result=await do_task(task_data)
                #print(result)
            except Exception as e:
                print(f"任务失败: {e}")
            finally:
                self.task_queue.task_done()

if __name__ == "__main__":
    async def main():
        manager = BaseImageManager()
        manager.start_task_worker()
        await manager.put_image_to_screen("测试任务")
        await manager.put_image_to_screen("测试任务2")
        await asyncio.sleep(20)

    asyncio.run(main())
    