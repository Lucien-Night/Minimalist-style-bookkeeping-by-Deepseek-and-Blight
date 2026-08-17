# 一键重新打包小账本 exe
# 用法：在 bookkeeping 目录下执行 .\rebuild.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\.venv\Scripts\pyinstaller.exe)) {
    Write-Host "未找到 .venv，请先执行：" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv"
    Write-Host "  .venv\Scripts\python -m pip install pywebview pyinstaller pillow"
    exit 1
}

.\.venv\Scripts\pyinstaller.exe --noconfirm --clean --onefile --windowed `
    --name 小账本 `
    --icon "$PSScriptRoot\src\app.ico" `
    --add-data "$PSScriptRoot\src\index.html;." `
    --add-data "$PSScriptRoot\src\chart.umd.min.js;." `
    --add-data "$PSScriptRoot\src\quotes.txt;." `
    --distpath "$PSScriptRoot\dist" `
    --workpath "$PSScriptRoot\build" `
    --specpath "$PSScriptRoot\build" `
    "$PSScriptRoot\src\main.py"

if ($LASTEXITCODE -eq 0) {
    Copy-Item "$PSScriptRoot\dist\小账本.exe" "$PSScriptRoot\小账本.exe" -Force
    Write-Host "打包完成: $PSScriptRoot\小账本.exe" -ForegroundColor Green
}
