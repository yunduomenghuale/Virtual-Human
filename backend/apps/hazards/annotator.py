"""把 bbox 百分比绘制为红框 + 序号标签。"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Tuple

from PIL import Image, ImageDraw, ImageFont


SEVERITY_COLOR = {
    'low': (255, 200, 0, 220),
    'medium': (255, 120, 0, 230),
    'high': (220, 30, 30, 240),
}
DEFAULT_COLOR = (220, 30, 30, 240)


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/msyhbd.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def annotate(image_path: str | Path, hazards: List[Dict[str, Any]],
             output_path: str | Path) -> Tuple[int, int]:
    """绘制红框,返回 (width, height)。"""
    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(image_path).convert('RGBA')
    width, height = img.size
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    line_w = max(3, int(min(width, height) * 0.005))
    font_size = max(16, int(min(width, height) * 0.025))
    font = _load_font(font_size)

    for idx, hz in enumerate(hazards, start=1):
        bbox_pct = hz.get('bbox') or [0, 0, 100, 100]
        if len(bbox_pct) != 4:
            bbox_pct = [0, 0, 100, 100]
        x_pct, y_pct, w_pct, h_pct = bbox_pct
        x1 = int(width * x_pct / 100.0)
        y1 = int(height * y_pct / 100.0)
        x2 = int(width * (x_pct + w_pct) / 100.0)
        y2 = int(height * (y_pct + h_pct) / 100.0)
        x1, x2 = max(0, min(x1, x2)), min(width, max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(height, max(y1, y2))
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue

        color = SEVERITY_COLOR.get(hz.get('severity', 'medium'), DEFAULT_COLOR)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_w)

        # 标签
        label = f'{idx}. {hz.get("name", "")}'
        # 计算文本框
        try:
            tb = draw.textbbox((0, 0), label, font=font)
            tw, th = tb[2] - tb[0], tb[3] - tb[1]
        except AttributeError:
            tw, th = font.getsize(label)
        pad = 6
        ly1 = max(0, y1 - th - pad * 2)
        ly2 = ly1 + th + pad * 2
        lx1 = x1
        lx2 = min(width, x1 + tw + pad * 2)
        draw.rectangle([lx1, ly1, lx2, ly2], fill=color)
        draw.text((lx1 + pad, ly1 + pad), label, fill=(255, 255, 255, 255), font=font)

    out = Image.alpha_composite(img, overlay).convert('RGB')
    out.save(output_path, format='JPEG', quality=92)
    return width, height
