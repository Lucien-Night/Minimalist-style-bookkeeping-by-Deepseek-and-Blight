# 小账本错位排查：启动 exe → 截图(正常) → 最大化 → 截图(全屏) → 关闭
$ErrorActionPreference = "Continue"
$exe   = "C:\work\bookkeeping\小账本.exe"
$shot1 = "C:\work\bookkeeping\shot_normal.png"
$shot2 = "C:\work\bookkeeping\shot_max.png"
$info  = "C:\work\bookkeeping\shot_info.txt"

Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Cap {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmd);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
  [DllImport("gdi32.dll")] public static extern bool BitBlt(IntPtr hdcDst, int x, int y, int w, int h, IntPtr hdcSrc, int sx, int sy, uint rop);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@

function Save-Shot([IntPtr]$hwnd, [string]$path) {
  $r = New-Object Cap+RECT
  [Cap]::GetWindowRect($hwnd, [ref]$r) | Out-Null
  $w = $r.Right - $r.Left
  $h = $r.Bottom - $r.Top
  if ($w -le 0 -or $h -le 0) { return "invalid rect" }
  $bmp = New-Object System.Drawing.Bitmap($w, $h)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $hdcDst = $g.GetHdc()
  $hdcSrc = [Cap]::GetDC([IntPtr]::Zero)
  [Cap]::BitBlt($hdcDst, 0, 0, $w, $h, $hdcSrc, $r.Left, $r.Top, 0x00CC0020) | Out-Null
  $g.ReleaseHdc($hdcDst)
  [Cap]::ReleaseDC([IntPtr]::Zero, $hdcSrc) | Out-Null
  $g.Dispose()
  $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose()
  return "rect=${w}x${h} dpi=$([Cap]::GetDpiForWindow($hwnd))"
}

$log = @()

# 1. 关闭旧实例
Get-Process | Where-Object { $_.Path -eq $exe } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. 启动新实例
$p = Start-Process -FilePath $exe -PassThru
$hwnd = [IntPtr]::Zero
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Milliseconds 500
  if ($p.HasExited) { $log += "exe exited early code=$($p.ExitCode)"; break }
  if ($p.MainWindowHandle -ne 0) { $hwnd = $p.MainWindowHandle; break }
}
if ($hwnd -eq [IntPtr]::Zero) {
  $log += "NO WINDOW"
  $log | Out-File $info -Encoding UTF8
  Write-Host "FAILED: no window found"
  exit 1
}
$log += "window found, waiting for page render..."
Start-Sleep -Seconds 12

# 3. 正常窗口截图
$log += "normal: " + (Save-Shot $hwnd $shot1)

# 4. 最大化并截图
[Cap]::ShowWindow($hwnd, 3) | Out-Null
Start-Sleep -Seconds 5
$log += "maximized: " + (Save-Shot $hwnd $shot2)

# 5. 关闭应用
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
$log += "done"
$log | Out-File $info -Encoding UTF8
Write-Host "DONE. Files saved to C:\work\bookkeeping\shot_normal.png and shot_max.png"
