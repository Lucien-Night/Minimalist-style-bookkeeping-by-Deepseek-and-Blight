# -*- coding: utf-8 -*-
"""生成应用图标 app.ico：蓝色圆角方块 + 白色 ¥ 符号。"""
from PIL import Image, ImageDraw, ImageFont

SIZE = 256


def make_tile(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 圆角背景 + 轻微渐变感（用两层色块模拟）
    radius = int(size * 0.22)
    d.rounded_rectangle([2, 2, size - 2, size - 2], radius=radius, fill=(0, 113, 227, 255))
    d.rounded_rectangle([2, 2, size - 2, size // 2 + radius], radius=radius,
                        fill=(0, 122, 240, 255))
    # 底部叠加一层更深色，形成自上而下的渐变
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([2, size // 2 - radius, size - 2, size - 2], radius=radius,
                         fill=(0, 90, 200, 120))
    img = Image.alpha_composite(img, overlay)
    return img


def draw_yen(img: Image.Image) -> Image.Image:
    d = ImageDraw.Draw(img)
    size = img.width
    cx = size / 2
    top = size * 0.26
    bottom = size * 0.74
    stroke = int(size * 0.055)
    bar_y = size * 0.55
    # 尝试用字体绘制 ¥；失败则退化为笔画
    try:
        font = ImageFont.truetype("msyhbd.ttc", int(size * 0.62))
    except Exception:
        font = None
    if font is not None:
        d.text((cx, size * 0.20), "\u00a5", font=font, fill=(255, 255, 255, 255), anchor="mm")
        return img
    # 退化方案：两条斜臂 + 竖线 + 两条横杠
    d.line([(cx - size * 0.16, top), (cx, size * 0.42)], fill="white", width=stroke)
    d.line([(cx + size * 0.16, top), (cx, size * 0.42)], fill="white", width=stroke)
    d.line([(cx, size * 0.32), (cx, bottom)], fill="white", width=stroke)
    d.line([(cx - size * 0.2, bar_y), (cx + size * 0.2, bar_y)], fill="white", width=stroke)
    d.line([(cx - size * 0.14, bar_y + size * 0.12), (cx + size * 0.14, bar_y + size * 0.12)],
           fill="white", width=stroke)
    return img


icon = make_tile(SIZE)
icon = draw_yen(icon)
icon.save(r"C:\work\bookkeeping\src\app.ico",
          format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon saved")
