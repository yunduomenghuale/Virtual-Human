from django.conf import settings
from django.db import models


class Report(models.Model):
    """实验室消防安全检查报告。"""
    SEVERITY_CHOICES = [('low', '低'), ('medium', '中'), ('high', '高')]

    title = models.CharField('报告标题', max_length=200)
    lab_name = models.CharField('实验室名称', max_length=128, db_index=True,
                                blank=True, default='')
    lab = models.ForeignKey(
        'labs.Lab', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='实验室',
        related_name='reports',
    )
    other_location = models.CharField('其他地点', max_length=128, blank=True, default='')
    address = models.CharField('检查地址', max_length=200, blank=True, default='')
    inspector = models.CharField('检查人', max_length=64, blank=True, default='')

    detections = models.ManyToManyField('hazards.HazardDetection', blank=True,
                                        related_name='reports')

    summary_stats = models.JSONField('汇总统计', default=dict,
                                     help_text='{total, by_severity, by_category}')
    agent_evaluation = models.TextField('agent 评价', blank=True, default='')
    references = models.JSONField('参考依据', default=list,
                                  help_text='[{title, snippet}]')
    extra_notes = models.TextField('备注', blank=True, default='')

    pdf_file = models.FileField('PDF', upload_to='reports/pdf/', blank=True, null=True)
    docx_file = models.FileField('DOCX', upload_to='reports/docx/', blank=True, null=True)

    overall_severity = models.CharField('总体风险', max_length=10,
                                        choices=SEVERITY_CHOICES, default='medium')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '报告'
        verbose_name_plural = '报告'
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        # 有 lab 外键时同步 lab_name；无外键时保留已设置的 lab_name（如通过 build_report 传入）
        if self.lab:
            self.lab_name = self.lab.name
        elif not self.lab_name:
            self.lab_name = self.other_location or ''
        super().save(*args, **kwargs)
