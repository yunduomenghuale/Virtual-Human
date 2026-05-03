from rest_framework import viewsets, status, decorators, response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.common.permissions import IsAdmin
from apps.skill_permissions.services import get_role_skills, ensure_defaults
from .models import User
from .serializers import (UserSerializer, LoginSerializer,
                          ChangePasswordSerializer, issue_tokens)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data['user']
        return response.Response(issue_tokens(user))


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields = ('username', 'real_name', 'lab_name')
    filterset_fields = ('role', 'is_active')

    @decorators.action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        ensure_defaults()
        u = request.user
        return response.Response({
            'id': u.id, 'username': u.username,
            'real_name': u.real_name, 'lab_name': u.lab_name,
            'lab': u.lab_id,
            'other_location': u.other_location,
            'role': u.role, 'role_label': u.role_label,
            'skills': get_role_skills(u.role),
        })

    @decorators.action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        ser = ChangePasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        u = request.user
        if not u.check_password(ser.validated_data['old_password']):
            return response.Response({'detail': '原密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        u.set_password(ser.validated_data['new_password'])
        u.save()
        return response.Response({'detail': '密码已更新'})
