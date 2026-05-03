from rest_framework import viewsets, decorators, response, status
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsAdmin
from .models import SkillPermission, SkillCode
from .serializers import SkillPermissionSerializer
from .services import ensure_defaults


class SkillPermissionViewSet(viewsets.ModelViewSet):
    queryset = SkillPermission.objects.all().order_by('role', 'skill')
    serializer_class = SkillPermissionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    http_method_names = ['get', 'patch', 'post']

    @decorators.action(detail=False, methods=['post'])
    def reset_defaults(self, request):
        SkillPermission.objects.all().delete()
        ensure_defaults()
        return response.Response({'detail': '已恢复默认权限矩阵'})

    @decorators.action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def matrix(self, request):
        ensure_defaults()
        data = {}
        for perm in SkillPermission.objects.all():
            data.setdefault(perm.role, {})[perm.skill] = perm.enabled
        skills_meta = [{'code': s.value, 'label': s.label} for s in SkillCode]
        return response.Response({'matrix': data, 'skills': skills_meta})
