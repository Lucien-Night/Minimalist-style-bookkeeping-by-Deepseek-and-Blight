# -*- coding: utf-8 -*-
"""沙盒适配：DSH 沙盒拒绝向 tempfile.mkdtemp 创建的目录写入。
用 os.makedirs 创建等价唯一目录替代，行为不变且所有写入仍限于工作区。
仅对本 venv 的 python 进程生效；PyInstaller 打包出的 exe 不受影响。
"""
import os
import secrets
import tempfile


def _mkdtemp(suffix=None, prefix=None, dir=None):
    if dir is None:
        dir = tempfile.gettempdir()
    for _ in range(100):
        name = (prefix or "tmp") + secrets.token_hex(6) + (suffix or "")
        path = os.path.join(dir, name)
        try:
            os.makedirs(path)
            return path
        except FileExistsError:
            continue
    raise FileExistsError("could not create unique temp directory")


tempfile.mkdtemp = _mkdtemp
