@echo off
rem 小账本错位排查：一键截图（约 25 秒，请勿操作鼠标键盘）
chcp 65001 >nul
echo 正在启动小账本并截图，请稍候（约 25 秒，期间请勿操作）...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0capture.ps1"
echo.
echo 截图完成。请回到对话中告诉我，我来分析截图。
pause
