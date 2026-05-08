from django.conf import settings
from django.db import models


class HazardDetection(models.Model):
    """一次图片上传 + 一次隐患识别。"""
    SEVERITY_CHOICES = [('low', '低'), ('medium', '中'), ('high', '高')]
    MEDIA_TYPE_CHOICES = [('image', '图片'), ('video', '视频')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='hazard_detections')
    lab_name = models.CharField('实验室', max_length=128, blank=True, default='')
    lab = models.ForeignKey(
        'labs.Lab', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='实验室',
        related_name='hazard_detections',
    )
    other_location = models.CharField('其他地点', max_length=128, blank=True, default='')
    media_type = models.CharField('媒体类型', max_length=10, choices=MEDIA_TYPE_CHOICES,
                                  default='image')
    original_image = models.FileField('原始媒体', upload_to='hazards/original/')
    cover_image = models.ImageField('封面图', upload_to='hazards/covers/',
                                    blank=True, null=True)
    annotated_image = models.ImageField('标注图片', upload_to='hazards/annotated/',
                                        blank=True, null=True)
    summary = models.TextField('整体评估', blank=True, default='')
    overall_severity = models.CharField('总体风险', max_length=10, choices=SEVERITY_CHOICES,
                                        default='medium')
    hazards = models.JSONField('隐患明细', default=list,
                               help_text='[{name, category, severity, description, suggestion, bbox}]')
    image_width = models.IntegerField('图片宽', default=0)
    image_height = models.IntegerField('图片高', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '隐患识别'
        verbose_name_plural = '隐患识别'
        ordering = ('-created_at',)

    @property
    def hazard_count(self) -> int:
        return len(self.hazards or [])

    def save(self, *args, **kwargs):
        self.lab_name = self.lab.name if self.lab else (self.other_location or '')
        super().save(*args, **kwargs)
