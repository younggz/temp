from django.contrib import admin
from .models import ChatLog, FailedLog, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'tags', 'created_time')
    list_filter = ('created_time', 'category')
    search_fields = ('title', 'content', 'tags')
    ordering = ('-created_time',)


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_input', 'predicted_intent', 'confidence', 'algorithm', 'is_helpful', 'created_time')
    list_filter = ('predicted_intent', 'algorithm', 'is_helpful', 'created_time')
    search_fields = ('user__username', 'user_input', 'response_text')
    ordering = ('-created_time',)


@admin.register(FailedLog)
class FailedLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_input', 'predicted_intent', 'confidence', 'is_corrected', 'created_time')
    list_filter = ('predicted_intent', 'is_corrected', 'created_time')
    search_fields = ('user__username', 'user_input')
    ordering = ('-created_time',)
