from django.conf import settings
from django.db import models


class Lab(models.Model):
    name = models.CharField('名称', max_length=128, unique=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='负责人',
        related_name='managed_labs',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '实验室'
        verbose_name_plural = '实验室'
        ordering = ('name',)

    def __str__(self):
        return self.name
