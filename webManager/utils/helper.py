import importlib
import yaml
import asyncio
from concurrent.futures import ThreadPoolExecutor
import anyio
import cv2
import numpy as np
import mediapipe as mp

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


def face_boxes_from_image(img_rgb, model_selection=0, min_conf=0.5):
    h, w = img_rgb.shape[:2]
    #img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    with mp.solutions.face_detection.FaceDetection(
        model_selection=model_selection, min_detection_confidence=min_conf
    ) as fd:
        res = fd.process(img_rgb)
    boxes = []
    if res.detections:
        for det in res.detections:
            rb = det.location_data.relative_bounding_box
            x1 = int(rb.xmin * w)
            y1 = int(rb.ymin * h)
            x2 = int((rb.xmin + rb.width)  * w)
            y2 = int((rb.ymin + rb.height) * h)
            boxes.append([x1, y1, x2, y2])
    return boxes




def region_metrics_3x3(img, max_side=640, bins=16,
                       edge_thresh1=80, edge_thresh2=160,
                       weights=None,
                       boxes=None,            # 新增：待“避让”的框（列表，每个[x1,y1,x2,y2]，像素坐标）
                       box_policy="center",   # "center" 或 "iou"
                       iou_thr=0.1            # 当 policy="iou" 时的判定阈值
                       ):
    """
    3x3 九宫格区域打分；若传入 boxes，则包含这些 boxes 的区域优先级靠后。
    img: BGR (OpenCV)
    boxes: list of [x1,y1,x2,y2] (像素坐标, 与 img 对齐的坐标系)
    box_policy:
        - "center": 以 box 中心点落入区域判定该区域被占用
        - "iou":    若 box 与区域的 IoU > iou_thr 判定被占用
    """

    if weights is None:
        weights = dict(color_std=1.0, entropy=1.0, edge_density=1.0, lap_var=1.0)
    if boxes is None:
        boxes = []

    # --- 轻量化缩放（注意：只用于特征计算；占用判定仍基于原图坐标！） ---
    H0, W0 = img.shape[:2]
    scale = float(max_side) / max(H0, W0)
    if scale < 1.0:
        img_small = cv2.resize(img, (int(W0 * scale), int(H0 * scale)), interpolation=cv2.INTER_AREA)
    else:
        img_small = img
        scale = 1.0
    h, w = img_small.shape[:2]

    # --- 3x3 九宫格切分（小图坐标） ---
    cxs = [0, w // 3, (2 * w) // 3, w]
    cys = [0, h // 3, (2 * h) // 3, h]
    grid_names = [
        ["left_top",   "mid_top",   "right_top"],
        ["left_mid",   "mid_mid",   "right_mid"],
        ["left_bottom","mid_bottom","right_bottom"],
    ]

    # 小图中每个区域的 box（x1,y1,x2,y2）
    regions_small = {}
    for r in range(3):
        for c in range(3):
            name = grid_names[r][c]
            x1, x2 = cxs[c], cxs[c + 1]
            y1, y2 = cys[r], cys[r + 1]
            if x2 <= x1: x2 = min(x1 + 1, w)
            if y2 <= y1: y2 = min(y1 + 1, h)
            regions_small[name] = (x1, y1, x2, y2)

    # 同时给出对应“原图坐标”的区域（便于和 boxes 判定）
    inv = 1.0 / scale
    regions_full = {
        k: (int(x1 * inv), int(y1 * inv), int(x2 * inv), int(y2 * inv))
        for k, (x1, y1, x2, y2) in regions_small.items()
    }

    # --- 预计算特征（小图） ---
    hsv  = cv2.cvtColor(img_small, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
    max_entropy = np.log2(bins)

    def iou(a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
        inter = iw * ih
        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
        union = area_a + area_b - inter + 1e-6
        return inter / union

    def center_in(box, region):
        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        rx1, ry1, rx2, ry2 = region
        return (rx1 <= cx < rx2) and (ry1 <= cy < ry2)

    results = {}

    # 先逐块计算“内容特征”
    for name, (sx1, sy1, sx2, sy2) in regions_small.items():
        roi_hsv  = hsv[sy1:sy2, sx1:sx2]
        roi_gray = gray[sy1:sy2, sx1:sx2]
        if roi_gray.size == 0:
            results[name] = dict(
                box=regions_full[name],
                color_std=0.0, entropy=0.0, edge_density=0.0, lap_var=0.0,
                monotone_score=0.0, rich_score=0.0,
                occupied=False
            )
            continue

        h_std = float(roi_hsv[:, :, 0].std())
        s_std = float(roi_hsv[:, :, 1].std())
        v_std = float(roi_hsv[:, :, 2].std())
        color_var = (h_std + s_std + v_std) / 3.0

        hist = cv2.calcHist([roi_gray], [0], None, [bins], [0, 256]).flatten()
        p = hist / (hist.sum() + 1e-8)
        entropy = float(-(p * np.log2(p + 1e-12)).sum())
        entropy_n = entropy / (max_entropy + 1e-8)

        edges = cv2.Canny(roi_gray, edge_thresh1, edge_thresh2, L2gradient=False)
        edge_density = float(edges.mean()) / 255.0

        lap = cv2.Laplacian(roi_gray, cv2.CV_32F)
        lap_var = float(lap.var())
        lap_sqrt = np.sqrt(lap_var + 1e-6)

        rich_score = (
            weights["color_std"]    * color_var   +
            weights["entropy"]      * entropy_n   +
            weights["edge_density"] * edge_density+
            weights["lap_var"]      * lap_sqrt
        )
        monotone_score = (
            weights["color_std"]    * (1.0 / (color_var + 1e-6)) +
            weights["entropy"]      * (1.0 - entropy_n)         +
            weights["edge_density"] * (1.0 - edge_density)      +
            weights["lap_var"]      * (1.0 / (lap_sqrt + 1e-6))
        )

        results[name] = dict(
            box=regions_full[name],          # 原图坐标系下的区域框
            color_std=color_var,
            entropy=entropy,
            edge_density=edge_density,
            lap_var=lap_var,
            monotone_score=float(monotone_score),
            rich_score=float(rich_score),
            occupied=False                   # 先标 False，下一步判定
        )

    # --- 判定哪些区域被 boxes 占用（用原图坐标） ---
    if boxes:
        for name, r_full in regions_full.items():
            occ = False
            for b in boxes:
                if box_policy == "center":
                    if center_in(b, r_full):
                        occ = True; break
                else:  # "iou"
                    if iou(b, r_full) > iou_thr:
                        occ = True; break
            results[name]["occupied"] = occ

    # --- 生成两套排序 ---
    # 1) 按“丰富度”从低到高（你原来的 sorted_by_rich）
    base_sorted = [k for k, _ in sorted(results.items(), key=lambda kv: kv[1]["rich_score"])]

    # 2) 将 occupied=True 的区域降级到末尾，且保持各自相对顺序
    not_occ = [k for k in base_sorted if not results[k]["occupied"]]
    occ     = [k for k in base_sorted if results[k]["occupied"]]
    sorted_pref = not_occ + occ

    return results, base_sorted, sorted_pref