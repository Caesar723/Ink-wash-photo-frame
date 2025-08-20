# Ink-wash-photo-frame

# 可扩展模块

此相框的显示是可以扩展的，可以添加衍生不同的模块，比如：
- 天气模块
- 时间模块
- 新闻模块
- 股票模块
- 汇率模块

扩展方法如下

## 创建HTML文件

模块的显示是基于网页的，所以需要创建一个HTML文件，这个HTML文件是模块的显示页面。软件会在后台对HTML文件进行渲染然后截图。

在`webManager/templates`目录下创建一个HTML文件，文件名格式为`module_name.html`，比如`weather.html`。

把相关的 css 和 js 文件放到`webManager/static`目录下，文件名格式为`module_name.css`和`module_name.js`，比如`weather.css`和`weather.js`。

图片可以放到`webManager/static/images/image_frame`目录下。

HTML文件访问特定文件时
- 图片：`static/images/image_frame`
- css：`static/css/module_name.css`
- js：`static/js/module_name.js`





## 创建Python文件

在`webManager/modules`目录下创建一个Python文件，文件名格式为`module_name.py`，比如`weather.py`。

Python文件需要继承`BaseImageCreator`类，并实现`create_image`方法。

### create_image

```python
async def create_image(self):
    base_url = f"http://0.0.0.0:{self.config['basic_port']}/module_name"
    params = {
        "params1": value1,
    }
    url = f"{base_url}?{urlencode(params)}"
    image=await self.url_to_image(url)
    return image
```

create_image 方法会返回一个PIL.Image.

你可以在这里加入你的逻辑，比如调用API获取数据，然后根据数据生成图片。

参数可以通过urlencode 方法进行编码，然后拼接在url后面。

your_url可以在`webManager/router/page.py`文件中配置。


## webManager/router/page.py

在这里你可以添加对应的接口，举一个例子:

```python
@router.get("/module_name")
async def module_name(request: Request):
    return appServer.templates.TemplateResponse(
        "module_name.html", 
        {
        "request": request,
        }
    )
```

## 配置文件(config/basic.yaml)

在这里需要把模块添加到`module_dict`列表中，如果觉得看不清，可以先在 `config/basic copy.yaml`文件中编辑再复制黏贴到`config/basic.yaml`文件中。


`module_dict`字典中，key是模块的名称，value是模块的类名。
如：
```yaml
module_dict:
  "模块名称": "webManager.module.module_name.ModuleName"
```

`module_used`列表中，是模块的名称,不填代表不使用，填了代表使用，如：
```yaml
module_used:
  - "模块名称"
```


这样一个模块就添加好了。
