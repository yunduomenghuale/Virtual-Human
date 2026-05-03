"""skill 权限默认表 + 查询服务。"""
from __future__ import annotations
from typing import Dict, List

from .models import SkillPermission, SkillCode


# 默认权限配置(对应文档.md 角色矩阵)
DEFAULT_MATRIX: Dict[str, List[str]] = {
    'admin': [SkillCode.KNOWLEDGE_QA, SkillCode.REPORT_GEN,
              SkillCode.HAZARD_DETECT, SkillCode.ANALYTICS],
    'safety_officer': [SkillCode.KNOWLEDGE_QA, SkillCode.REPORT_GEN,
                       SkillCode.HAZARD_DETECT],
    'experimenter': [SkillCode.KNOWLEDGE_QA, SkillCode.HAZARD_DETECT],
}


def ensure_defaults() -> None:
    """确保默认权限存在(幂等)。"""
    for role, skills in DEFAULT_MATRIX.items():
        all_skills = [s.value for s in SkillCode]
        for skill in all_skills:
            SkillPermission.objects.get_or_create(
                role=role, skill=skill,
                defaults={'enabled': skill in skills},
            )


def is_skill_enabled(role: str, skill: str) -> bool:
    try:
        return SkillPermission.objects.get(role=role, skill=skill).enabled
    except SkillPermission.DoesNotExist:
        return skill in DEFAULT_MATRIX.get(role, [])


def get_role_skills(role: str) -> List[str]:
    perms = SkillPermission.objects.filter(role=role, enabled=True).values_list('skill', flat=True)
    return list(perms)
