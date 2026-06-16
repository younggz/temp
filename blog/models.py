from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    """博客文章模型。"""
    title = models.CharField(max_length=200, verbose_name='文章标题')
    content = models.TextField(verbose_name='文章内容')
    tags = models.CharField(max_length=500, blank=True, default='', verbose_name='标签，逗号分隔')
    category = models.CharField(max_length=100, blank=True, default='', verbose_name='分类')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        ordering = ['-created_time']
        verbose_name = '博客文章'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title

    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class FailedLog(models.Model):
    """低置信度或识别失败日志，用于后续意图识别优化。"""
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='用户')
    user_input = models.CharField(max_length=200, verbose_name='用户输入')
    predicted_intent = models.CharField(max_length=50, verbose_name='预测意图', null=True, blank=True)
    confidence = models.FloatField(verbose_name='置信度', default=0.0)
    is_corrected = models.BooleanField(verbose_name='是否已人工纠正', default=False)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        ordering = ['-created_time']
        verbose_name = '意图识别失败日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user_input} ({self.predicted_intent})"


class ChatLog(models.Model):
    """每个用户与智能助手的一次对话，用于个性化分析和反馈闭环。"""
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='用户')
    user_input = models.CharField(max_length=500, verbose_name='用户输入')
    predicted_intent = models.CharField(max_length=50, verbose_name='预测意图', blank=True, default='')
    confidence = models.FloatField(verbose_name='意图置信度', default=0.0)
    algorithm = models.CharField(max_length=50, verbose_name='识别算法', blank=True, default='')
    response_text = models.TextField(verbose_name='助手回复', blank=True, default='')
    is_helpful = models.BooleanField(verbose_name='用户反馈是否有帮助', null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        ordering = ['-created_time']
        verbose_name = '用户对话日志'
        verbose_name_plural = verbose_name

    def __str__(self):
        username = self.user.username if self.user else 'anonymous'
        return f"{username}: {self.user_input} -> {self.predicted_intent}"
