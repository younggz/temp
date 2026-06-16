from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('', views.index, name='index'),
    path('posts/', views.post_list, name='post_list'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('search/', views.search, name='search'),
    path('share/', views.share, name='share'),
    path('share/qr.png', views.share_qr, name='share_qr'),
    path('nlp/chat/', views.nlp_chat, name='nlp_chat'),
    path('nlp/feedback/', views.feedback, name='feedback'),  # 新增反馈接口
    path('skill_demo/', views.skill_demo, name='skill_demo'),  # 技能适配演示
    path('skill_demo_api/', views.skill_demo_api, name='skill_demo_api'),  # 技能适配API
]
