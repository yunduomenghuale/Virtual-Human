from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import HasSkill, IsAdmin
from . import services


class DashboardView(APIView):
    """系统管理员看板。"""
    permission_classes = [IsAuthenticated, IsAdmin, HasSkill]
    required_skill = 'analytics'

    def get(self, request):
        return Response(services.dashboard())


class LabsView(APIView):
    """实验室列表 + 聚合统计。

    任何已登录用户都能看(供安全员 / 实验员选择实验室),
    若需要更严格的访问控制,把 IsAdmin 加到 permission_classes 即可。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'results': services.lab_overview()})
