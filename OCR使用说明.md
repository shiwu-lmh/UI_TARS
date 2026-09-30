# 截图批量 OCR 使用说明

本工具使用 PaddleOCR-VL 识别截图。你可以让 UI-TARS 把截图保存到 `screenshots` 文件夹，监控脚本会自动识别新文件，去掉重复文字，并持续更新 Markdown 文档。真实的服务地址和令牌只保存在本地 `ocr_config.json` 或环境变量中，不要提交到 Git。

## 准备截图

可以手动把截图放进 `screenshots` 文件夹，也可以让脚本自动截取当前桌面。支持 PNG、JPG、JPEG、WebP、BMP、TIF 和 TIFF。文件名中的数字会按自然顺序处理，例如 `page2.png` 会排在 `page10.png` 前面。

## 不生成安装包也可以运行

OCR 监控脚本不依赖 UI-TARS 安装包。只要有 Python 和有效的 Access Token，就可以直接运行：

```powershell
python .\watch_ocr.py .\screenshots
```

如果还需要从源码启动 UI-TARS，建议使用项目提供的启动脚本：

```powershell
cd .\UI-TARS-desktop-0.3.0
.\启动UI-TARS.ps1
```

这条命令会启动开发版 UI-TARS，不需要先生成 exe 安装包。


## 运行方式一：监控 UI-TARS 的截图文件夹（推荐）

先确认工作目录中的 `ocr_config.json` 使用公司内网配置，然后在 PowerShell 中运行：

```powershell
python .\watch_ocr.py .\screenshots
```

看到“正在监控”后，再在 UI-TARS 中发送类似这句话：

```text
把当前网页截图保存到 D:\liminghao\pycharm\file\UI_TARS_ocr\screenshots，文件名按顺序递增；截图完成后继续下一张。
```

每当文件夹里出现新的 PNG/JPG 图片，监控脚本就会自动调用 OCR，并更新：

```text
screenshots\截图 OCR 汇总.md
```

监控脚本会等待文件写入完成；按 `Ctrl+C` 停止。只处理现有图片一次可以使用：

```powershell
python .\watch_ocr.py .\screenshots --once
```

注意：监控脚本只能处理已经落盘的图片。如果 UI-TARS 只在界面中显示截图、没有真的保存成文件，需要先让 UI-TARS 执行保存文件的动作，或者手动把截图复制到该文件夹。

## 运行方式一（UI-TARS 快捷键自动落盘）

启动脚本会把 `UI_TARS_SCREENSHOT_DIR` 设置为项目的 `screenshots` 文件夹。UI-TARS 执行 `hotkey(key='win print')` 后，会把当前画面直接保存为 `page-001.png`、`page-002.png` 等文件，监控脚本会立即识别，不依赖 Windows 的“图片\屏幕截图”目录。

先开一个 PowerShell 窗口：

```powershell
python .\watch_ocr.py .\screenshots
```

然后给 UI-TARS 的任务说明写：

```text
处理当前网页时，每完成一屏就执行 hotkey(key='win print') 截图，然后继续向下滚动。不要使用 Win+Shift+S，因为它需要人工框选。
```

## 运行方式二（Windows 系统截图同步备用方案）

如果你希望使用 Windows 自己的截图文件，也可以运行下面的同步脚本。`Win+PrtScn` 必须真的在系统中生成文件，脚本才能复制它。

先开两个 PowerShell 窗口。

窗口一，同步 Windows 截图：

```powershell
python .\sync_windows_screenshots.py
```

窗口二，自动 OCR：

```powershell
python .\watch_ocr.py .\screenshots
```

然后给 UI-TARS 的任务说明写：

```text
处理当前网页时，每完成一屏就执行 hotkey(key='win print') 截图，然后继续向下滚动。不要使用 Win+Shift+S，因为它需要人工框选。
```

同步脚本会把系统截图复制为 `page-001.png`、`page-002.png` 等文件，OCR 监控脚本随后会自动解析并合并去重。

## 运行方式二：批量处理已经存在的截图

如果需要切换回百度官方在线 API，`ocr_config.json` 可以使用下面的配置：

```json
{
  "base_url": "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs",
  "api_mode": "official-api",
  "model": "PaddleOCR-VL",
  "access_token": "你的 AI Studio Access Token"
}
```

公司内网 OpenAI 兼容接口配置如下；程序会自动请求 `/v1/chat/completions`：

```json
{
  "base_url": "https://your-ocr-service.example.com/v1",
  "api_mode": "openai-compatible",
  "model": "PaddleOCR-VL-1.6-0.9B",
  "access_token": ""
}
```

然后在 PowerShell 中切换到工作目录，运行：

```powershell
python .\ocr_screenshots.py .\screenshots
```

Access Token 需要在百度 AI Studio 的 PaddleOCR API 页面获取。官方文档说明在线 API 使用 Bearer Token 鉴权，并通过异步任务返回结果。

若不想把 Token 以明文保存在 JSON 文件，可以使用环境变量：

```powershell
$env:PADDLEOCR_ACCESS_TOKEN = "你的 AI Studio Access Token"
python .\ocr_screenshots.py .\screenshots
```

也可以使用环境变量设置模型名称：

```powershell
$env:PADDLEOCR_MODEL = "PaddleOCR-VL-1.6-0.9B"
python .\ocr_screenshots.py .\screenshots
```

指定输出文件时添加 `--output`：

```powershell
python .\ocr_screenshots.py .\screenshots --output .\识别结果.md
```

## 运行方式三：由 Python 截取当前桌面后立即 OCR

只有在你明确需要 Python 自己截屏时才使用下面命令：

```powershell
python .\ocr_screenshots.py --capture --output .\当前屏幕 OCR.md
```

该命令会先把当前桌面保存为 `screenshots\自动截图.png`，然后提交这张图片进行 OCR。

默认结果保存在截图文件夹里的 `截图 OCR 汇总.md`。识别失败的图片会显示错误，脚本会继续处理剩余图片，并把成功结果写入文档。

## 接口文档

[PaddleOCR 官方在线 API 文档](https://www.paddleocr.ai/latest/en/version3.x/inference_deployment/serving/paddleocr_official_api/python.html)
