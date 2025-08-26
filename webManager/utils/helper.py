import importlib
import yaml
import asyncio
from concurrent.futures import ThreadPoolExecutor
import anyio
import cv2
import numpy as np


executor = ThreadPoolExecutor(max_workers=5)

async def do_task(task):# func
    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(executor, task)



def task_wrapper(func):
    def wrapper(*args, **kwargs):
        def start():
            return func(*args, **kwargs)
        return start
    return wrapper



class ConfigWrapper:
    def __init__(self,config,file_path):
        self.config=config
        self.file_path=file_path

        self.flag=True
        self._batch_depth = 0
        self._lock = anyio.Lock()

    def __setitem__(self, key, value):
        self.config[key]=value
        if self._batch_depth == 0:
            self._save_sync_or_async()
            
        return self.config[key]

    def __getitem__(self, key):
        return self.config[key]
    
    def __delitem__(self, key):
        del self.config[key]

        if self._batch_depth == 0:
            self._save_sync_or_async()
        return self.config[key]


    def __enter__(self):
        # 同步上下文：进入批处理（可嵌套）
        self._batch_depth += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 退出一层；最后一层退出时统一保存
        self._batch_depth -= 1
        if self._batch_depth == 0:
            self._save_sync_or_async()
        # 返回 False 让异常继续抛出（如有）
        return False

    async def __aenter__(self):
        # 用锁保护批处理深度的修改，避免并行进入时竞争
        async with self._lock:
            self._batch_depth += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        must_flush = False
        async with self._lock:
            self._batch_depth -= 1
            if self._batch_depth == 0:
                must_flush = True
        if must_flush:
            await self._save_async()

        return False

    def _save_sync_or_async(self):
        """
        在同步环境里直接阻塞式保存；
        若当前在事件循环中，则把阻塞 I/O 丢到线程池，避免卡住主循环。
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 不在事件循环 -> 同步保存
            save_yaml(self.file_path,self.config)
        else:
            # 在事件循环里 -> 异步丢线程池
            # 不 await 是同步路径；但确保不会并发写：交给 _lock/深度来兜底
            loop.create_task(self._save_async())

    async def _save_async(self):
        """
        异步安全保存：串行执行，避免并发写。
        """
        async with self._lock:
            # 把阻塞的 save 放到线程池里执行
            await asyncio.to_thread(save_yaml, self.file_path, self.config)

    
def read_yaml(file):
    with open(file, 'r', encoding="utf-8") as f:
        data = yaml.safe_load( f )
    return ConfigWrapper(data,file) 


def save_yaml(file, data):
    with open(file, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)


def get_class_by_name(class_name):
    path = class_name.split(".") 
    if len(path) == 1:
        raise ValueError(f"Please provide package path: [{class_name}]") 
    
    package = importlib.import_module( ".".join(path[:-1]) ) 
    class_handler = getattr(package, path[-1]) 
    return class_handler 



def region_metrics(img):
    # 轻量化：先把图像宽边缩到 640（树莓派可改小到 320）
    h, w = img.shape[:2]
    scale = 640.0 / max(h, w)
    if scale < 1.0:
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]

    # 划分 5 块：左上、右上、左下、右下、中间
    cx, cy = w // 2, h // 2
    # 中间区域取宽高的 1/3，可按需调整
    cw, ch = w // 3, h // 3
    mx1, my1 = cx - cw // 2, cy - ch // 2
    mx2, my2 = mx1 + cw, my1 + ch

    regions = {
        "left_top":     (0,      0,      cx,     cy),
        "right_top":    (cx,     0,      w,      cy),
        "left_bottom":  (0,      cy,     cx,     h),
        "right_bottom": (cx,     cy,     w,      h),
        "center":       (mx1,    my1,    mx2,    my2),
    }

    results = {}

    # 预备：转 HSV 和灰度（后面重复使用）
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    for name, (x1, y1, x2, y2) in regions.items():
        roi_bgr  = img[y1:y2, x1:x2]
        roi_hsv  = hsv[y1:y2, x1:x2]
        roi_gray = gray[y1:y2, x1:x2]

        # 1) 颜色方差（在 HSV 上更稳健）
        #    使用 H、S、V 三通道的标准差，再取均值作为色彩变化量
        h_std = float(roi_hsv[:, :, 0].std())
        s_std = float(roi_hsv[:, :, 1].std())
        v_std = float(roi_hsv[:, :, 2].std())
        color_var = (h_std + s_std + v_std) / 3.0

        # 2) 亮度熵（灰度直方图 16 bins，轻量）
        hist = cv2.calcHist([roi_gray], [0], None, [16], [0, 256]).flatten()
        p = hist / (hist.sum() + 1e-8)
        entropy = float(-np.sum(p * np.log2(p + 1e-12)))

        # 3) 边缘密度（Canny）
        edges = cv2.Canny(roi_gray, 80, 160, L2gradient=False)
        edge_density = float(edges.mean()) / 255.0  # 0~1：白像素比例

        # 4) 拉普拉斯方差（纹理强度）
        lap = cv2.Laplacian(roi_gray, cv2.CV_32F)
        lap_var = float(lap.var())

        # 组合分数：
        # 单调分：颜色方差低 + 熵低 + 边缘少 + 纹理弱
        # 丰富分：颜色方差高 + 熵高 + 边缘多 + 纹理强
        # 为避免数值量纲不一致，这里做一个简单的归一化/缩放权重（可按数据分布再调）
        # 注意：这些权重是经验值，可按你的图像做微调
        monotone_score = (
            (1.0 / (color_var + 1e-6)) * 1.0 +
            (1.0 / (entropy   + 1e-6)) * 1.0 +
            (1.0 - edge_density)       * 1.0 +
            (1.0 / (np.sqrt(lap_var + 1e-6))) * 1.0
        )

        rich_score = (
            color_var   * 1.0 +
            entropy     * 1.0 +
            edge_density* 1.0 +
            np.sqrt(lap_var + 1e-6) * 1.0
        )

        results[name] = dict(
            box=(x1, y1, x2, y2),
            color_std=color_var,
            entropy=entropy,
            edge_density=edge_density,
            lap_var=lap_var,
            monotone_score=monotone_score,
            rich_score=rich_score,
        )

    # 找出最单调/最丰富的区域
    sorted_results = [item[0] for item in sorted(results.items(), key=lambda kv: kv[1]["rich_score"])]


    return results, sorted_results
