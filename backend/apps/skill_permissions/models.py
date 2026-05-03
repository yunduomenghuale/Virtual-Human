from django.db import models


class SkillCode(models.TextChoices):
    KNOWLEDGE_QA = 'knowledge_qa', '基础知识库问答'
    REPORT_GEN = 'report_gen', '报告生成'
    HAZARD_DETECT = 'hazard_detect', '隐患识别'
    ANALYTICS = 'analytics', '数据分析'


class SkillPermission(models.Model):
    """每个 (角色, skill) 一条记录,enabled 由系统管理员开关。"""
    role = models.CharField(max_length=32)
    skill = models.CharField(max_length=32, choices=SkillCode.choices)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('role', 'skill')
        verbose_name = 'Skill 权限'
        verbose_name_plural = 'Skill 权限'

    def __str__(self) -> str:
        return f'{self.role}:{self.skill}={self.enabled}'
