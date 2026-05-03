from rest_framework import serializers
from .models import SkillPermission, SkillCode


class SkillPermissionSerializer(serializers.ModelSerializer):
    skill_label = serializers.SerializerMethodField()

    class Meta:
        model = SkillPermission
        fields = ('id', 'role', 'skill', 'skill_label', 'enabled', 'updated_at')
        read_only_fields = ('updated_at',)

    def get_skill_label(self, obj):
        return SkillCode(obj.skill).label
