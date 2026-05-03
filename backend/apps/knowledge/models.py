from django.conf import settings
from django.db import models


class KnowledgeDocument(models.Model):
    title = models.CharField('标题', max_length=200)
    source = models.CharField('来源标识', max_length=200, unique=True,
                              help_text='用于在向量库中删除该文档相关的全部 chunk')
    description = models.CharField('描述', max_length=500, blank=True, default='')
    chunk_count = models.IntegerField('片段数', default=0)
    file = models.FileField('原始文件', upload_to='knowledge_base/', blank=True, null=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '知识库文档'
        verbose_name_plural = '知识库文档'
        ordering = ('-created_at',)

    def __str__(self):
        return self.title


class QASession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='qa_sessions')
    question = models.TextField('问题')
    answer = models.TextField('回答')
    sources = models.JSONField('引用片段', default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '问答记录'
        verbose_name_plural = '问答记录'
        ordering = ('-created_at',)
