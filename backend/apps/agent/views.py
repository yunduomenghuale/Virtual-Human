"""Agent /chat/ 端点。"""
from __future__ import annotations
import json
import logging

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
      attachment  — 可选,单张图片文件(hazard_detect 会消费它)
      attachments — 可选,多张图片文件,与 attachment 兼容

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

        attachments = []
        attachments.extend(request.FILES.getlist('attachments'))
        attachments.extend(request.FILES.getlist('videos'))
        legacy_attachment = request.FILES.get('attachment')
        if legacy_attachment:
            attachments.append(legacy_attachment)

        try:
            result = services.chat(
                user=request.user,
                messages=messages,
                attachment=attachments[0] if len(attachments) == 1 else None,
                attachments=attachments,
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
