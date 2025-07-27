


class BaseHookManager:
    instance_list=[]
    def __init__(self):
        self.instance_list.append(self)


    