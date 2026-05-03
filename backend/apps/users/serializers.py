from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.skill_permissions.services import get_role_skills, ensure_defaults
from .models import User, Role


class UserSerializer(serializers.ModelSerializer):
    role_label = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def get_role_label(self, obj):
        return obj.role_label

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'real_name', 'lab_name', 'lab', 'other_location',
                  'role', 'role_label', 'is_active', 'date_joined')
        read_only_fields = ('id', 'date_joined', 'role_label', 'lab_name')

    def create(self, validated_data):
        password = validated_data.pop('password', None) or 'changeme'
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError('用户名或密码错误')
        attrs['user'] = user
        return attrs


def issue_tokens(user: User) -> dict:
    ensure_defaults()
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'lab_name': user.lab_name,
            'role': user.role,
            'role_label': user.role_label,
            'skills': get_role_skills(user.role),
        },
    }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)
