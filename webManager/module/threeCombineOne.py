from PIL import Image


from utils.baseImageCreator import BaseImageCreator

class ThreeCombineOne(BaseImageCreator):
    def __init__(self,config):
        self.config=config

    def when_config_change(self):
        pass

    async def create_image(self):
        pass