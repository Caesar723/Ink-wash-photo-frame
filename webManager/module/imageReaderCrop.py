import os
from PIL import Image,ImageOps,ImageEnhance
import asyncio
import math
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webManager.utils.baseImageCreator import BaseImageCreator
from webManager.utils.helper import read_yaml



class ImageReaderCrop(BaseImageCreator):
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
        saturation_factor = 2  # 提高饱和度 50%
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation_factor)
        print("enhance",image.size)
        if self.config["target_img_size"][0]==800:
            image= image.rotate(-90, expand=True)
        else:
            image= image.rotate(180, expand=True)
        return image

    def image_preprocess(self, image, mode: str = "center", upscale: bool = True):
        """
        通过缩放+裁剪得到固定大小图像（保持宽高比）。
        :param image: PIL.Image
        :param mode:  裁剪对齐方式，可选：
                    'center'（默认），'top', 'bottom', 'left', 'right',
                    'top-left', 'top-right', 'bottom-left', 'bottom-right'
        :param upscale: 是否允许放大（原图比目标小的时候）。不允许则可能无法覆盖目标尺寸。
        :return: PIL.Image（大小为 config['target_img_size']）
        """
        print(image.size)
        target_height, target_width = self.config["target_img_size"]
        original_width, original_height = image.size

        # 为兼容 Pillow 新旧版本的 LANCZOS
        Resampling = getattr(Image, "Resampling", Image)
        resample = Resampling.LANCZOS

        # 缩放比例：为覆盖目标，用 max（让短边也能到达目标）
        scale = max(target_width / original_width, target_height / original_height)

        if not upscale:
            # 不允许放大时，最多保持 1.0；如果仍不足以覆盖，后续会报错或可选择改为填充
            scale = min(1.0, scale)

        new_w = max(1, int(math.ceil(original_width * scale)))
        new_h = max(1, int(math.ceil(original_height * scale)))

        resized = image.resize((new_w, new_h), resample=resample)

        
        if new_w < target_width or new_h < target_height:
            return ImageOps.pad(image, (target_width, target_height), method=resample, color=(0,0,0), centering=(0.5,0.5))

        # 计算裁剪起点（根据对齐方式）
        def get_offsets(mode_str: str):
            # 水平
            if "left" in mode_str:
                left = 0
            elif "right" in mode_str:
                left = new_w - target_width
            else:  # center / top / bottom
                left = (new_w - target_width) // 2

            # 垂直
            if "top" in mode_str:
                top = 0
            elif "bottom" in mode_str:
                top = new_h - target_height
            else:  # center / left / right
                top = (new_h - target_height) // 2

            # 边界保护
            left = max(0, min(left, new_w - target_width))
            top = max(0, min(top, new_h - target_height))
            return left, top

        left, top = get_offsets(mode.lower())
        box = (left, top, left + target_width, top + target_height)
        out = resized.crop(box)
        print(out.size)
        
        return out


    
if __name__ == "__main__":

    async def main():
        print(sys.path)
        config=read_yaml("webManager/config/basic.yaml")
        image_reader=ImageReaderCrop(config)
        image=await image_reader.create_image()
        image=image_reader.image_final_process(image)

        image.show()

    asyncio.run(main())
