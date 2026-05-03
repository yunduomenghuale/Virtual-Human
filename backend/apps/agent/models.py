import uuid
from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        verbose_name='用户',
    )
    title = models.CharField('标题', max_length=255, blank=True, default='新对话')
    messages = models.JSONField('消息记录', default=list)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '对话会话'
        verbose_name_plural = '对话会话'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.title} ({self.user.username})'
