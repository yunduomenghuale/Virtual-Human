"""隐患识别业务流:多模态 LLM 识别 → 落库。"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from PIL import Image

from apps.common.llm import get_vision_llm
from .models import HazardDetection


def detect_and_annotate(user, image_file, lab_name: str = '',
                        extra_instruction: str = '') -> HazardDetection:
    """主入口:接收上传的图片 -> 多模态模型识别 -> 持久化。"""
    detection = HazardDetection.objects.create(
        user=user, lab_name=lab_name, original_image=image_file,
    )
    original_path = Path(detection.original_image.path)

    # 1. 多模态 LLM 识别(不再要求 bbox)
    result = get_vision_llm().detect_hazards(original_path, extra_instruction=extra_instruction)
    detection.summary = result.get('summary', '')
    detection.overall_severity = result.get('overall_severity', 'medium')
    detection.hazards = result.get('hazards', [])

    # 2. 记录图片尺寸
    try:
        with Image.open(original_path) as img:
            detection.image_width, detection.image_height = img.size
    except Exception:
        pass

    detection.save()
    return detection
