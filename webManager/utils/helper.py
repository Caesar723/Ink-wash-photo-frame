import importlib
import yaml
import asyncio
from concurrent.futures import ThreadPoolExecutor
import anyio

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