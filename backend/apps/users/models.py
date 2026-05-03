from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = 'admin', '系统管理员'
    SAFETY_OFFICER = 'safety_officer', '实验室管理员/安全员'
    EXPERIMENTER = 'experimenter', '实验人员'


class User(AbstractUser):
    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.EXPERIMENTER,
    )
    real_name = models.CharField('真实姓名', max_length=64, blank=True, default='')
    lab_name = models.CharField('所属实验室', max_length=128, blank=True, default='')
    lab = models.ForeignKey(
        'labs.Lab', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='实验室',
        related_name='users',
    )
    other_location = models.CharField('其他地点', max_length=128, blank=True, default='')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    @property
    def role_label(self) -> str:
        return Role(self.role).label

    def save(self, *args, **kwargs):
        self.lab_name = self.lab.name if self.lab else (self.other_location or '')
        super().save(*args, **kwargs)
