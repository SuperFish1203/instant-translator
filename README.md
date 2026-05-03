# Instant Translator

Windows 即时翻译桌面工具。

## 功能

- 后台常驻系统托盘
- 全局快捷键 `Alt+T`
- 模拟复制并在翻译后恢复原剪贴板
- 弹出轻量翻译窗口，仅显示译文
- 支持 OpenAI 兼容接口、Google Translate、Tencent Translate
- 设置界面可配置源语言模式、目标语言和各服务商参数

## 开发运行

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe src\instant_translator\app.py
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 打包为 Windows EXE

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --name InstantTranslator --paths src src\instant_translator\app.py
```

打包产物默认位于：

`dist\InstantTranslator\InstantTranslator.exe`
