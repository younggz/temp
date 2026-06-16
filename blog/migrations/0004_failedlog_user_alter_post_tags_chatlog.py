# Generated for multi-user assistant records.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0003_post_category_post_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='failedlog',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='用户'),
        ),
        migrations.AlterField(
            model_name='post',
            name='tags',
            field=models.CharField(blank=True, default='', max_length=500, verbose_name='标签，逗号分隔'),
        ),
        migrations.CreateModel(
            name='ChatLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_input', models.CharField(max_length=500, verbose_name='用户输入')),
                ('predicted_intent', models.CharField(blank=True, default='', max_length=50, verbose_name='预测意图')),
                ('confidence', models.FloatField(default=0.0, verbose_name='意图置信度')),
                ('algorithm', models.CharField(blank=True, default='', max_length=50, verbose_name='识别算法')),
                ('response_text', models.TextField(blank=True, default='', verbose_name='助手回复')),
                ('is_helpful', models.BooleanField(blank=True, null=True, verbose_name='用户反馈是否有帮助')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='记录时间')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户对话日志',
                'verbose_name_plural': '用户对话日志',
                'ordering': ['-created_time'],
            },
        ),
    ]
