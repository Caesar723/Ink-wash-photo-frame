import importlib
import yaml
import asyncio
from concurrent.futures import ThreadPoolExecutor


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

    def __setitem__(self, key, value):
        self.config[key]=value
        save_yaml(self.file_path,self.config)
        return self.config[key]

    def __getitem__(self, key):
        return self.config[key]
    
    def __delitem__(self, key):
        del self.config[key]
        save_yaml(self.file_path,self.config)
        return self.config[key]

    
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