# -*- coding: utf-8 -*-
r"""小账本 —— 桌面版入口（pywebview + WebView2）。

将原本的单页记账页面 (index.html) 包装为 Windows 桌面应用，
账目数据通过 js_api 桥接持久化到本地 JSON 文件：
    %APPDATA%\bookkeeping\data.json
"""
import json
import logging
import os
import random
import sys
import traceback
from pathlib import Path

# ── DPI 修复 ──
# 175% 等非 100% 缩放下，WinForms 主机的自动缩放会导致 WebView2 画布与
# DOM 文字渲染错位。这里：1) 启用 Per-Monitor V2 DPI 感知（必须在创建任何
# 窗口之前调用）；2) 稍后禁用表单的 AutoScale（见 _patch_dpi_autoscale）。
import ctypes

try:
    # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        pass

# 数据目录：固定放在 %APPDATA%\bookkeeping
DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "bookkeeping"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "data.json"

# 诊断日志（即时落盘，便于排查问题）
class _FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


log_handler = _FlushFileHandler(DATA_DIR / "app.log", encoding="utf-8")
log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
root_logger = logging.getLogger()
root_logger.addHandler(log_handler)
root_logger.setLevel(logging.DEBUG)

import webview  # noqa: E402


def _patch_dpi_autoscale():
    """禁用 pywebview WinForms 表单的自动缩放。

    高 DPI（如 175%）下 AutoScaleMode.Dpi 会对 WebView2 控件重复缩放，
    造成画布内容与 DOM 布局错位（最典型的就是饼图圆心文字偏移）。
    """
    try:
        from webview.platforms import winforms as _wf
        from System.Windows.Forms import AutoScaleMode as _ASM

        _orig_init = _wf.BrowserView.BrowserForm.__init__

        def _init(self, *args, **kwargs):
            _orig_init(self, *args, **kwargs)
            try:
                self.AutoScaleMode = getattr(_ASM, "None")
            except Exception:
                pass

        _wf.BrowserView.BrowserForm.__init__ = _init
    except Exception:
        pass


def app_dir() -> Path:
    """打包后为 PyInstaller 解包目录，开发时为脚本所在目录。"""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent))


def quotes_folder() -> Path:
    """独立名言文件夹：exe 同目录下的 quotes 文件夹（随软件一起存放、可自行编辑）。"""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "quotes"


QUOTES_DIR = quotes_folder()
QUOTES_FILE = QUOTES_DIR / "quotes.txt"


def _ui_file_dialog(save: bool, default_name: str = "") -> str | None:
    """线程安全地弹出保存/打开文件对话框。

    js_api 运行在后台线程，WinForms 对话框必须在 UI 线程打开，
    因此通过表单 Invoke 调度。返回所选路径，取消返回 None。
    """
    try:
        from webview.platforms import winforms as _wf
        from System import Action
        from System.Windows.Forms import DialogResult, OpenFileDialog, SaveFileDialog

        form = list(_wf.BrowserView.instances.values())[0]
        result = {}

        def _show():
            if save:
                dlg = SaveFileDialog()
                dlg.Filter = "CSV 文件 (*.csv)|*.csv"
                dlg.FileName = default_name or "小账本导出.csv"
                dlg.OverwritePrompt = True
                dlg.AddExtension = True
                dlg.DefaultExt = "csv"
                if dlg.ShowDialog(form) == DialogResult.OK:
                    result["path"] = dlg.FileName
            else:
                dlg = OpenFileDialog()
                dlg.Filter = "CSV 文件 (*.csv)|*.csv|所有文件 (*.*)|*.*"
                dlg.Multiselect = False
                dlg.RestoreDirectory = True
                if dlg.ShowDialog(form) == DialogResult.OK:
                    result["path"] = dlg.FileName

        if form.InvokeRequired:
            form.Invoke(Action(_show))
        else:
            _show()
        return result.get("path")
    except Exception:
        traceback.print_exc()
        return None


def ensure_quotes():
    """确保外部名言文件夹存在；缺失时用内置的 200 条名言重建。"""
    try:
        QUOTES_DIR.mkdir(parents=True, exist_ok=True)
        if not QUOTES_FILE.exists():
            bundled = app_dir() / "quotes.txt"
            if bundled.exists():
                QUOTES_FILE.write_text(
                    bundled.read_text(encoding="utf-8"), encoding="utf-8"
                )
    except Exception:
        traceback.print_exc()


class Api:
    """暴露给前端 JS 的接口（window.pywebview.api）。"""

    def save(self, payload: str) -> bool:
        try:
            # 先写临时文件再替换，避免写入中断导致数据损坏
            tmp = DATA_FILE.with_suffix(".json.tmp")
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(DATA_FILE)
            return True
        except Exception:
            traceback.print_exc()
            return False

    def load(self):
        try:
            if DATA_FILE.exists():
                return DATA_FILE.read_text(encoding="utf-8")
        except Exception:
            traceback.print_exc()
        return None

    def get_quote(self) -> str:
        """从独立 quotes 文件夹中随机取一条名言。"""
        ensure_quotes()
        try:
            raw = QUOTES_FILE.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                raw = QUOTES_FILE.read_text(encoding="gbk", errors="ignore")
            except Exception:
                raw = ""
        except Exception:
            raw = ""
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if not lines:
            return "量入为出，适度消费。——《增广贤文》"
        return random.choice(lines)

    def export_file(self, filename: str, content: str) -> str:
        """弹出保存对话框导出 CSV。返回 ok / cancelled / error。"""
        path = _ui_file_dialog(save=True, default_name=filename)
        if not path:
            return "cancelled"
        try:
            # utf-8-sig（带 BOM），保证 Excel/WPS 正确识别中文
            Path(path).write_bytes(content.encode("utf-8-sig"))
            return "ok"
        except Exception:
            traceback.print_exc()
            return "error"

    def import_file(self) -> str:
        """弹出打开对话框读取 CSV 内容。取消时返回空字符串。"""
        path = _ui_file_dialog(save=False)
        if not path:
            return ""
        try:
            data = Path(path).read_bytes()
            for enc in ("utf-8-sig", "utf-8", "gbk"):
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="ignore")
        except Exception:
            traceback.print_exc()
            return ""


def main():
    _patch_dpi_autoscale()
    ensure_quotes()
    index = app_dir() / "index.html"
    api = Api()
    webview.create_window(
        "小账本",
        str(index),
        js_api=api,
        width=1200,
        height=800,
        min_size=(960, 640),
        background_color="#f5f5f7",
    )
    webview.start(
        debug=False,
        # 指定 WebView2 用户数据目录，保证 localStorage 持久化
        storage_path=str(DATA_DIR / "webview2"),
        private_mode=False,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        (DATA_DIR / "error.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
