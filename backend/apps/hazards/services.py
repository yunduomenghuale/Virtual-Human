"""隐患识别业务流:多模态 LLM 识别 → 落库。"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path

from django.core.files import File
from PIL import Image

from apps.common.llm import get_vision_llm
from apps.common.notifier import send_high_risk_alert
from .models import HazardDetection


def _generate_video_cover(detection: HazardDetection, video_path: Path) -> None:
    """从视频中抽一帧作为封面。OpenCV 不可用或视频异常时静默跳过。"""
    try:
        import cv2
        import numpy as np
    except Exception:
        return

    cap = cv2.VideoCapture(str(video_path))
    try:
        if not cap.isOpened():
            return
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if frame_count > 10:
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(10, frame_count - 1))
        ok, frame = cap.read()
        if not ok or frame is None:
            return
        # cv2.imwrite 对中文路径支持不好，改用 PIL + BytesIO
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        buf = BytesIO()
        pil_img.save(buf, format='JPEG', quality=85)
        buf.seek(0)
        filename = f'{video_path.stem}_cover.jpg'
        detection.cover_image.save(filename, File(buf), save=False)
    finally:
        cap.release()


def detect_and_annotate(user, image_file, lab_name: str = '',
                        extra_instruction: str = '', media_type: str = 'image') -> HazardDetection:
    """主入口:接收上传的图片/视频 -> 多模态模型识别 -> 持久化。"""
    detection = HazardDetection.objects.create(
        user=user, lab_name=lab_name, original_image=image_file, media_type=media_type,
    )
    original_path = Path(detection.original_image.path)
    if media_type == 'video':
        _generate_video_cover(detection, original_path)

    # 1. 多模态 LLM 识别(不再要求 bbox)
    if media_type == 'video':
        result = get_vision_llm().detect_hazards_in_video(
            original_path, extra_instruction=extra_instruction,
        )
    else:
        result = get_vision_llm().detect_hazards(original_path, extra_instruction=extra_instruction)
    detection.summary = result.get('summary', '')
    detection.overall_severity = result.get('overall_severity', 'medium')
    detection.hazards = result.get('hazards', [])

    # 2. 记录图片尺寸
    if media_type == 'image':
        try:
            with Image.open(original_path) as img:
                detection.image_width, detection.image_height = img.size
        except Exception:
            pass

    detection.save()

    # 3. 高风险时推送通知
    if detection.overall_severity == 'high':
        send_high_risk_alert(detection)

    return detection
