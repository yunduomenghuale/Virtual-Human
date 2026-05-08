"""通知服务: 企业微信机器人推送等。"""
from __future__ import annotations
import json
import logging
import threading
from typing import Optional

import requests
from django.conf import settings

from apps.hazards.models import HazardDetection

logger = logging.getLogger(__name__)


def _build_wechat_markdown(detection: HazardDetection) -> dict:
    """构造企业微信 markdown 消息体。"""
    lab = detection.lab_name or '未填写'
    severity_label = {'low': '低', 'medium': '中', 'high': '高'}.get(detection.overall_severity, detection.overall_severity)
    hazards = detection.hazards or []
    hazard_names = [h.get('name', '未命名') for h in hazards[:3]]
    hazard_text = '、'.join(hazard_names) if hazard_names else '详见系统'
    cover_url = detection.cover_image.url if detection.cover_image else (detection.original_image.url if detection.original_image else '')
    detail_url = f"{settings.BASE_URL or ''}/hazards/history"

    content = (
        f"<@all>\n"
        f"## ⚠️ 智安平台高风险预警\n\n"
        f"> **风险等级:** <font color='red'>{severity_label}</font>\n"
        f"> **实验室:** {lab}\n"
        f"> **隐患数:** {len(hazards)} 项\n"
        f"> **主要隐患:** {hazard_text}\n\n"
        f"[查看详情]({detail_url})"
    )

    msg = {
        'msgtype': 'markdown',
        'markdown': {'content': content},
    }
    if cover_url:
        msg['markdown']['content'] += f"\n\n<img src='{cover_url}' width='300' />"
    return msg


def _send_wechat_webhook(payload: dict) -> None:
    """同步发送 HTTP POST 到企业微信 webhook。"""
    url = getattr(settings, 'WECHAT_WEBHOOK_URL', '')
    if not url:
        return
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get('errcode') != 0:
            logger.warning('企业微信推送失败: %s', result)
    except Exception as exc:
        logger.warning('企业微信推送异常: %s', exc)


def send_wechat_alert(detection: HazardDetection) -> None:
    """推送高风险预警到企业微信机器人。"""
    if detection.overall_severity != 'high':
        return
    payload = _build_wechat_markdown(detection)
    threading.Thread(target=_send_wechat_webhook, args=(payload,), daemon=True).start()


def send_high_risk_alert(detection: HazardDetection) -> None:
    """统一入口: 高风险时发送所有配置的通知渠道。"""
    send_wechat_alert(detection)
