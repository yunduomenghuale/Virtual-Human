"""统一的 LLM 客户端封装,支持文本模型 + 视觉模型双通道。

无 API Key 时自动降级为 mock,方便离线 / 演示。
"""
from __future__ import annotations
import base64
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def _build_client(api_key: str, base_url: str):
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning('初始化 OpenAI 客户端失败: %s', exc)
        return None


class TextLLM:
    """文本生成模型 - 用于知识问答 / 报告生成 / agent 评价."""

    def __init__(self):
        self.model = settings.TEXT_LLM_MODEL
        self.client = _build_client(settings.TEXT_LLM_API_KEY, settings.TEXT_LLM_BASE_URL)

    @property
    def available(self) -> bool:
        return self.client is not None

    def _choose_model(self, override: Optional[str] = None) -> str:
        return override or self.model

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
             max_tokens: int = 1024, model: Optional[str] = None) -> str:
        if not self.available:
            return self._mock(messages)
        try:
            resp = self.client.chat.completions.create(
                model=self._choose_model(model),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ''
        except Exception as exc:  # noqa: BLE001
            logger.exception('文本 LLM 调用失败: %s', exc)
            return f'[LLM 调用失败: {exc}] 已降级返回。'

    def chat_stream(self, messages: List[Dict[str, str]], temperature: float = 0.3,
                    max_tokens: int = 1024, model: Optional[str] = None):
        """流式生成,逐 token yield 字符串片段。"""
        if not self.available:
            yield self._mock(messages)
            return
        try:
            resp = self.client.chat.completions.create(
                model=self._choose_model(model),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta.content or ''
                if delta:
                    yield delta
        except Exception as exc:  # noqa: BLE001
            logger.exception('文本 LLM 流式调用失败: %s', exc)
            yield f'[LLM 流式调用失败: {exc}]'

    def chat_with_tools(self, messages: List[Dict[str, Any]],
                        tools: List[Dict[str, Any]],
                        temperature: float = 0.2,
                        max_tokens: int = 1500):
        """Tool-calling 调用,返回 OpenAI ChatCompletionMessage(或 _MockMessage)。

        调用方应检查 .tool_calls 是否非空:非空 -> 需要执行工具并继续循环;
        否则 .content 即为最终回答。
        """
        if not self.available:
            # 离线 mock:不能真正派发工具,只能返回文本
            return _MockMessage(content=self._mock(messages))
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice='auto',
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message
        except Exception as exc:  # noqa: BLE001
            logger.exception('文本 LLM tool-calling 失败: %s', exc)
            return _MockMessage(content=f'[LLM 调用失败: {exc}] 已降级返回。')

    @staticmethod
    def _mock(messages: List[Dict[str, str]]) -> str:
        last = next((m for m in reversed(messages) if m.get('role') == 'user'), None)
        q = last['content'] if last else ''
        if '总结' in q or '评价' in q:
            return ('【Mock 评价】本次排查覆盖度较好,建议持续关注电气线路、化学品存放规范及'
                    '应急通道畅通,定期复查整改情况。')
        if '隐患' in q or '消防' in q:
            return ('【Mock 回答】实验室常见消防隐患包括:1) 电气线路老化或私拉乱接;'
                    '2) 易燃化学品未分类存放;3) 灭火器材失效或被遮挡;4) 应急照明 / 疏散指示损坏;'
                    '5) 消防通道堆物。建议参照 GB 50016《建筑设计防火规范》开展整改。')
        return f'【Mock 回答】已收到问题:{q[:80]}……(配置 TEXT_LLM_API_KEY 后可获得真实回答)'


# ===== 视觉 LLM =====
HAZARD_DETECT_PROMPT = (
    '请扮演实验室消防安全专家,仔细分析这张图片,识别其中可能存在的消防 / 安全隐患。'
    '\n严格按以下 JSON 格式输出,不要附加任何额外文字、markdown 或解释:'
    '\n{\n'
    '  "summary": "整体评估,1-2 句",\n'
    '  "overall_severity": "low | medium | high",\n'
    '  "hazards": [\n'
    '    {\n'
    '      "name": "隐患简称(不超过 12 字)",\n'
    '      "category": "电气|化学品|通道|灭火器|防护|通风|其他",\n'
    '      "severity": "low|medium|high",\n'
    '      "description": "1-3 句详细描述",\n'
    '      "suggestion": "整改建议"\n'
    '    }\n'
    '  ]\n'
    '}\n'
    '若图片明显不是实验室,返回 hazards 为空数组并在 summary 说明。'
)


class VisionLLM:
    """视觉理解模型 - 用于图片隐患识别."""

    def __init__(self):
        self.model = settings.VISION_LLM_MODEL
        self.client = _build_client(settings.VISION_LLM_API_KEY, settings.VISION_LLM_BASE_URL)

    @property
    def available(self) -> bool:
        return self.client is not None

    def detect_hazards(self, image_path: str | Path,
                       extra_instruction: str = '') -> Dict[str, Any]:
        """返回结构化的隐患识别结果。

        :return: {'summary': ..., 'overall_severity': ..., 'hazards': [...]}
        """
        if not self.available:
            return _mock_detection()
        try:
            data_url = self._to_data_url(image_path)
            user_blocks = [
                {'type': 'text', 'text': HAZARD_DETECT_PROMPT +
                 (f'\n\n补充说明:{extra_instruction}' if extra_instruction else '')},
                {'type': 'image_url', 'image_url': {'url': data_url}},
            ]
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': '你是实验室消防安全 AI,擅长识别图像中的安全隐患。'},
                    {'role': 'user', 'content': user_blocks},
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            text = resp.choices[0].message.content or ''
            return self._parse_json_payload(text)
        except Exception as exc:  # noqa: BLE001
            logger.exception('视觉 LLM 调用失败: %s', exc)
            mock = _mock_detection()
            mock['summary'] = f'[视觉模型调用失败,已降级 mock]{exc}'
            return mock

    @staticmethod
    def _to_data_url(path: str | Path) -> str:
        path = Path(path)
        ext = path.suffix.lower().lstrip('.')
        mime = 'image/jpeg' if ext in ('jpg', 'jpeg') else f'image/{ext or "png"}'
        with open(path, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode('ascii')
        return f'data:{mime};base64,{b64}'

    @staticmethod
    def _parse_json_payload(text: str) -> Dict[str, Any]:
        """从 LLM 输出中提取 JSON。"""
        # 直接尝试
        try:
            return _normalize_detection(json.loads(text))
        except Exception:
            pass
        # 抽取 ```json ... ``` 或第一个 {...}
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.S)
        if not m:
            m = re.search(r'(\{.*\})', text, re.S)
        if m:
            try:
                return _normalize_detection(json.loads(m.group(1)))
            except Exception as exc:  # noqa: BLE001
                logger.warning('JSON 解析失败: %s\n原文: %s', exc, text[:300])
        return {
            'summary': '视觉模型返回的内容无法解析为 JSON,以下是原始文本',
            'overall_severity': 'medium',
            'hazards': [],
            'raw': text,
        }


def _normalize_detection(data: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        'summary': str(data.get('summary', ''))[:500],
        'overall_severity': data.get('overall_severity', 'medium'),
        'hazards': [],
    }
    for h in data.get('hazards', []) or []:
        out['hazards'].append({
            'name': str(h.get('name', '未命名隐患'))[:80],
            'category': str(h.get('category', '其他'))[:20],
            'severity': h.get('severity', 'medium'),
            'description': str(h.get('description', ''))[:600],
            'suggestion': str(h.get('suggestion', ''))[:400],
        })
    return out


def _mock_detection() -> Dict[str, Any]:
    return {
        'summary': '【Mock 视觉分析】未配置 VISION_LLM_API_KEY,展示示例隐患。',
        'overall_severity': 'medium',
        'hazards': [
            {
                'name': '灭火器被遮挡',
                'category': '灭火器',
                'severity': 'high',
                'description': '灭火器前方堆放有杂物,紧急情况下取用受阻。',
                'suggestion': '清理灭火器周边 1m 范围内的所有杂物。',
                'bbox': [10, 55, 22, 35],
            },
            {
                'name': '电源插座过载',
                'category': '电气',
                'severity': 'medium',
                'description': '多个大功率设备插在同一排插上,存在过载发热风险。',
                'suggestion': '改用单独回路或加装漏电保护装置。',
                'bbox': [55, 30, 20, 18],
            },
            {
                'name': '化学品标签缺失',
                'category': '化学品',
                'severity': 'medium',
                'description': '操作台上的玻璃瓶标签模糊,无法识别内容。',
                'suggestion': '立即重新粘贴清晰标签,记录至化学品台账。',
                'bbox': [38, 62, 18, 22],
            },
        ],
    }


# ===== 单例 =====
_text_llm: Optional[TextLLM] = None
_vision_llm: Optional[VisionLLM] = None


def get_text_llm() -> TextLLM:
    global _text_llm
    if _text_llm is None:
        _text_llm = TextLLM()
    return _text_llm


class _MockMessage:
    """离线场景下的占位消息,模拟 OpenAI ChatCompletionMessage 形状。"""
    def __init__(self, content: str = '', tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or None
        self.role = 'assistant'

    def model_dump(self, **_):
        return {'role': self.role, 'content': self.content}


def get_vision_llm() -> VisionLLM:
    global _vision_llm
    if _vision_llm is None:
        _vision_llm = VisionLLM()
    return _vision_llm
