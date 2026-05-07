from django.db import models
import json

class TrainingMaterial(models.Model):
    STATUS_CHOICES = (
        ('pending', '等待处理'),
        ('processing', '解析中'),
        ('completed', '已完成'),
        ('failed', '解析失败'),
    )

    file = models.FileField(upload_to='training_materials/', verbose_name="原始文档")
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file_type = models.CharField(max_length=20, verbose_name="文件类型")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    error_message = models.TextField(null=True, blank=True, verbose_name="错误信息")
    
    raw_analysis = models.JSONField(null=True, blank=True, verbose_name="大模型原始解析结果")
    result_teaching = models.TextField(null=True, blank=True, verbose_name="生成的教学内容")
    result_scenarios = models.JSONField(null=True, blank=True, verbose_name="生成的场景题目")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scenario_training_material'
        verbose_name = "培训素材管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file_name

class FireScenario(models.Model):
    DIFFICULTY_CHOICES = (
        ('low', '低难度'),
        ('medium', '中难度'),
        ('high', '高难度'),
    )

    title = models.CharField(max_length=200, verbose_name="场景标题")
    topic = models.CharField(max_length=100, verbose_name="主题分类", help_text="例如: 电气火灾、违规动火等")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium', verbose_name="难度")
    
    teaching_content = models.TextField(null=True, blank=True, verbose_name="教学讲义内容", help_text="数字人先播报的教学内容")
    description = models.TextField(verbose_name="演练场景描述", help_text="用于向用户播报和展示的现场情况")
    image = models.ImageField(upload_to='scenarios/', null=True, blank=True, verbose_name="现场模拟图")
    
    material = models.ForeignKey(TrainingMaterial, on_delete=models.SET_NULL, null=True, blank=True, related_name='scenarios', verbose_name="所属素材")

    correct_actions = models.TextField(verbose_name="标准处置流程", help_text="供 Agent 评估用户回答的参考标准")
    analysis = models.TextField(verbose_name="案例分析总结", help_text="演练结束后给出的整体点评和原因分析")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'scenario_training_case'
        verbose_name = "消防演练场景"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title
