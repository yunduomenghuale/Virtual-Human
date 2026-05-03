"""DRF 权限类:基于角色 + skill_permissions 表的双层校验。"""
from __future__ import annotations
from rest_framework.permissions import BasePermission

from apps.skill_permissions.services import is_skill_enabled
from apps.users.models import Role


class IsAdmin(BasePermission):
    message = '需要系统管理员权限'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)


class HasSkill(BasePermission):
    """要求 view 设置 `required_skill` 属性,例如 'knowledge_qa'。"""
    message = '当前角色无该 skill 权限或该 skill 已被管理员禁用'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        skill = getattr(view, 'required_skill', None)
        if not skill:
            return True
        return is_skill_enabled(request.user.role, skill)


class IsAdminOrSafetyOfficer(BasePermission):
    message = '需要系统管理员或安全员权限'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role in ('admin', 'safety_officer')
