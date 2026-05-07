"""Agent /chat/ 端点。"""
from __future__ import annotations
import json
import logging
import time

import requests
from django.conf import settings
from rest_framework import parsers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import ChatSession
from .serializers import ChatSessionSerializer

logger = logging.getLogger(__name__)


class AgentChatView(APIView):
    """POST /api/agent/chat/

    请求(multipart/form-data):
      messages   — JSON 字符串,[{role, content}, ...]
      attachment — 可选,图片文件(hazard_detect 会消费它)

    或 application/json(无附件场景):
      { "messages": [{role, content}, ...] }
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)

    def post(self, request):
        raw_messages = request.data.get('messages')
        if isinstance(raw_messages, str):
            try:
                messages = json.loads(raw_messages)
            except json.JSONDecodeError:
                return Response({'detail': 'messages JSON 解析失败'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_messages, list):
            messages = raw_messages
        else:
            return Response({'detail': 'messages 必填(数组或 JSON 字符串)'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(messages, list) or not messages:
            return Response({'detail': 'messages 不能为空'},
                            status=status.HTTP_400_BAD_REQUEST)
        for m in messages:
            if not isinstance(m, dict) or 'role' not in m or 'content' not in m:
                return Response({'detail': 'messages 项必须包含 role 和 content'},
                                status=status.HTTP_400_BAD_REQUEST)

        attachment = request.FILES.get('attachment')

        try:
            result = services.chat(
                user=request.user,
                messages=messages,
                attachment=attachment,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception('Agent chat 失败: %s', exc)
            return Response({'detail': f'Agent 调用失败:{exc}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result)


class AgentSkillsView(APIView):
    """GET /api/agent/skills/  返回当前用户的可用 skill 列表(用于前端展示)。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .tools import list_skill_codes_for_user
        return Response({
            'enabled_skills': list_skill_codes_for_user(request.user),
        })


class ChatSessionViewSet(viewsets.ModelViewSet):
    """对话会话 CRUD。

    - 普通用户 / 安全员: 只能查看/操作自己的会话
    - 管理员: 可查看全部会话
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ChatSession.objects.all().select_related('user')
        if self.request.user.role != 'admin':
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AsrView(APIView):
    """POST /api/agent/asr/

    请求(multipart/form-data):
      audio — 音频文件(webm/wav 等)

    返回:
      { "text": "识别出的文字" }

    DashScope Paraformer 流程:
      1. 上传文件获取 file_id
      2. 创建 transcription 任务获取 job_id
      3. 轮询任务结果
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    DASHSCOPE_BASE = 'https://dashscope.aliyuncs.com/api/v1'
    POLL_INTERVAL = 1.5
    MAX_POLL = 20

    def post(self, request):
        audio = request.FILES.get('audio')
        if not audio:
            return Response({'detail': '请上传音频文件'}, status=status.HTTP_400_BAD_REQUEST)

        api_key = settings.ASR_API_KEY
        if not api_key:
            return Response({'detail': 'ASR 未配置'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            file_id = self._upload_file(audio, api_key)
            job_id = self._create_asr_job(file_id, api_key)
            text = self._poll_job(job_id, api_key)
            return Response({'text': text})
        except requests.RequestException as exc:
            logger.exception('ASR 调用失败: %s', exc)
            detail = getattr(exc.response, 'text', str(exc)) if hasattr(exc, 'response') else str(exc)
            return Response({'detail': f'语音识别失败: {detail}'}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:  # noqa: BLE001
            logger.exception('ASR 处理异常: %s', exc)
            return Response({'detail': f'语音识别失败: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _upload_file(self, audio, api_key: str) -> str:
        """Step 1: 上传音频文件到 DashScope 获取 file_id."""
        resp = requests.post(
            f'{self.DASHSCOPE_BASE}/files',
            headers={'Authorization': f'Bearer {api_key}'},
            files={'file': (audio.name, audio, audio.content_type or 'audio/webm')},
            data={'purpose': 'transcription'},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        uploaded = data.get('data', {}).get('uploaded_files', [])
        file_id = uploaded[0].get('file_id') if uploaded else None
        if not file_id:
            raise RuntimeError(f'文件上传未返回 id: {data}')
        return file_id

    def _create_asr_job(self, file_id: str, api_key: str) -> str:
        """Step 2: 创建语音识别任务."""
        resp = requests.post(
            f'{self.DASHSCOPE_BASE}/services/audio/asr/transcription',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': settings.ASR_MODEL or 'paraformer-v1',
                'input': {
                    'file_urls': [f'oss://{file_id}'],
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get('output', {}).get('task_id') or data.get('id')
        if not job_id:
            raise RuntimeError(f'创建 ASR 任务未返回 job_id: {data}')
        return job_id

    def _poll_job(self, job_id: str, api_key: str) -> str:
        """Step 3: 轮询任务结果直到成功或超时."""
        for _ in range(self.MAX_POLL):
            time.sleep(self.POLL_INTERVAL)
            resp = requests.get(
                f'{self.DASHSCOPE_BASE}/tasks/{job_id}',
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            job_status = data.get('output', {}).get('task_status', '').upper()
            if job_status == 'SUCCEEDED':
                results = data.get('output', {}).get('results', [])
                if results:
                    return results[0].get('transcription', '')
                return data.get('output', {}).get('transcription', '')
            if job_status in ('FAILED', 'ERROR', 'CANCELLED'):
                raise RuntimeError(f'ASR 任务失败: {data}')
        raise RuntimeError('ASR 任务轮询超时')
