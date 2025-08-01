import os
from PIL import Image
import asyncio

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webManager.utils.baseImageCreator import BaseImageCreator
from webManager.utils.helper import read_yaml



class ImageReader(BaseImageCreator):
    def __init__(self,config):
        self.config=config

    def when_config_change(self):
        pass

    async def create_image(self):
        self.image_path=self.get_image_path(self.config["basic_image_path"])
        
        image_path=os.path.join(self.config["basic_image_path"],self.image_path)
        image=self._read_pil(image_path)

        
        return image

    def image_final_process(self,image):
        if self.config["target_img_size"][0]==800:
            image= image.rotate(-90, expand=True)
        else:
            image= image.rotate(180, expand=True)
        return image


    
if __name__ == "__main__":

    async def main():
        print(sys.path)
        config=read_yaml("webManager/config/basic.yaml")
        image_reader=ImageReader(config)
        data=await image_reader.fetch_weather_and_forecast_async()
        print(data)

        

    asyncio.run(main())
