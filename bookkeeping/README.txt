小账本（桌面版）使用说明
========================

一、怎么用
----------
双击 小账本.exe 即可启动。界面与原网页版完全一致：
收支记录、本月统计、分类饼图（Chart.js 已本地化，完全离线可用）。

二、数据存在哪里
----------------
账目数据自动保存在：
    %APPDATA%\bookkeeping\data.json
（例如 C:\Users\你的用户名\AppData\Roaming\bookkeeping\data.json）

- 每添加/删除一条记录都会立即写入该文件，重新打开软件数据不会丢。
- 换电脑迁移数据：复制整个 %APPDATA%\bookkeeping 文件夹即可。
- 想备份：直接复制 data.json 一份保存。

三、底部名言
------------
页面底部每次启动随机显示一条记账/理财相关的名人名言与古诗词，
名言存放在独立的 quotes 文件夹（quotes\quotes.txt，共 200 条）：
- 可以直接用记事本编辑该文件（每行一条，格式：名言——出处）；
- 若该文件夹被删除，下次启动软件会自动重建默认的 200 条；
- 点击名言区域可随机换一条。

四、运行环境要求
----------------
- Windows 10 / 11（64 位）
- 系统自带的 .NET Framework 4.8 与 WebView2（Edge 内核）运行库，
  这两者在 Win10/11 上默认已具备，无需额外安装。

五、如何重新打包（修改页面后）
------------------------------
1. 安装 Python 3.14（64 位）。
2. 在本目录执行：
       python -m venv .venv
       .venv\Scripts\python -m pip install pywebview pyinstaller pillow
3. 双击运行 rebuild.ps1（或在 PowerShell 中执行 .\rebuild.ps1），
   完成后新的 exe 会生成在 dist\ 目录。

六、目录结构
------------
bookkeeping\
├─ 小账本.exe           可执行文件（单文件，绿色免安装）
├─ rebuild.ps1          一键重新打包脚本
├─ README.txt           本说明
├─ quotes\              独立名言文件夹（200 条，可自行编辑）
│  └─ quotes.txt
└─ src\                 源码
   ├─ index.html        记账页面（已适配桌面端）
   ├─ chart.umd.min.js  本地化图表库
   ├─ quotes.txt        内置名言（用于重建 quotes 文件夹）
   ├─ main.py           桌面窗口入口（pywebview + WebView2）
   ├─ make_icon.py      图标生成脚本
   ├─ app.ico           应用图标
   ├─ verify.ps1        启动自检脚本（开发用）
   └─ sitecustomize.py  受限沙盒环境重建时的补丁（正常环境无需理会）

技术说明：exe 由 PyInstaller 打包 Python 入口 + pywebview(WebView2) 加载
本地 index.html 而成；页面内通过 window.pywebview.api 桥接把数据写入本地
JSON 文件（浏览器中打开页面时自动回退为 localStorage 存储）。
