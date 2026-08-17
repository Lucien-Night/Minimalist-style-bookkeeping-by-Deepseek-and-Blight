# 验证脚本：启动打包好的 exe 并检查窗口/WebView2/存储是否正常
$ErrorActionPreference = "Continue"
$exe = Get-ChildItem "$PSScriptRoot\..\dist" -Filter *.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
if (-not $exe) { $exe = Get-ChildItem "$PSScriptRoot\.." -Filter *.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName }
if (-not $exe) { Write-Output "NO EXE FOUND"; exit 2 }
"EXE=$exe"
$env:APPDATA = "C:\work\bookkeeping\.testdata"
$env:TMP = "C:\work\bookkeeping\.tmp"
$env:TEMP = "C:\work\bookkeeping\.tmp"
Remove-Item C:\work\bookkeeping\.testdata -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item C:\work\bookkeeping\.tmp\_MEI* -Recurse -Force -ErrorAction SilentlyContinue

$p = Start-Process -FilePath $exe -PassThru
Start-Sleep -Seconds 18
if ($p.HasExited) {
    "ALIVE=False EXITCODE=$($p.ExitCode)"
} else {
    $win = Get-Process -Id $p.Id -ErrorAction SilentlyContinue | Select-Object MainWindowTitle
    "ALIVE=True TITLE=$($win.MainWindowTitle)"
}
$wv2 = Get-CimInstance Win32_Process -Filter "Name='msedgewebview2.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ParentProcessId -eq $p.Id }
"WEBVIEW2_CHILDREN=$(@($wv2).Count)"
"STORAGE_DIR_EXISTS=" + (Test-Path C:\work\bookkeeping\.testdata\bookkeeping\webview2)
if (Test-Path C:\work\bookkeeping\.testdata\bookkeeping\error.log) {
    "ERRORLOG:"
    Get-Content C:\work\bookkeeping\.testdata\bookkeeping\error.log -Tail 6
}
# 只清理本次启动的 WebView2 子进程和主进程
@($wv2) | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
