"""Create demo account and mock article data for deployment demos."""

import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')
django.setup()

from django.contrib.auth.models import User

from blog.models import ChatLog, Post
from nlp.relevance import rebuild_index


DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'Demo@123456'


ARTICLES = [
    {
        'title': 'Python 入门教程：从变量到函数',
        'tags': 'Python,入门,编程',
        'category': '编程语言',
        'content': '本文面向零基础学习者，讲解 Python 变量、数据类型、条件判断、循环和函数，适合作为编程入门的第一篇文章。',
    },
    {
        'title': 'Python 进阶：装饰器、生成器与上下文管理器',
        'tags': 'Python,进阶,编程',
        'category': '编程语言',
        'content': '本文介绍 Python 中常见的进阶语法，包括装饰器、生成器、迭代器和上下文管理器，帮助读者写出更优雅的代码。',
    },
    {
        'title': 'Django Web 开发实战：博客系统设计',
        'tags': 'Django,Python,Web',
        'category': 'Web开发',
        'content': '本文通过博客系统案例介绍 Django 的 MTV 架构、模型设计、路由、视图、模板和后台管理功能。',
    },
    {
        'title': 'Django 登录注册与用户权限管理',
        'tags': 'Django,登录,权限,用户系统',
        'category': 'Web开发',
        'content': '本文讲解如何使用 Django Auth 完成登录、注册、退出登录、用户权限控制和登录后访问限制。',
    },
    {
        'title': '自然语言处理 NLP 入门指南',
        'tags': 'NLP,自然语言处理,AI',
        'category': '人工智能',
        'content': '本文介绍 NLP 的基本概念、常见任务、分词、文本分类、问答系统和语义检索，为后续学习打基础。',
    },
    {
        'title': '意图识别算法详解：规则、相似度与集成方法',
        'tags': 'NLP,意图识别,算法',
        'category': '人工智能',
        'content': '本文比较关键词规则、SequenceMatcher、Jieba Jaccard 和集成算法在意图识别任务中的优缺点。',
    },
    {
        'title': 'V4 Darwin Ensemble 意图识别优化实践',
        'tags': 'NLP,达尔文优化,V4,算法评测',
        'category': '人工智能',
        'content': '本文介绍如何通过评测集、F1 分数、混淆矩阵和错误样本分析选择更优的意图识别算法。',
    },
    {
        'title': '机器学习入门：监督学习与无监督学习',
        'tags': '机器学习,入门,AI',
        'category': '人工智能',
        'content': '本文讲解监督学习、无监督学习、训练集、测试集、特征、标签和模型评估等机器学习基础概念。',
    },
    {
        'title': '深度学习基础：神经网络如何工作',
        'tags': '深度学习,神经网络,AI',
        'category': '人工智能',
        'content': '本文介绍神经网络、激活函数、损失函数、反向传播和梯度下降，适合深度学习初学者阅读。',
    },
    {
        'title': '大模型接入实践：OpenAI 兼容接口调用',
        'tags': '大模型,LLM,API,OpenAI',
        'category': '人工智能',
        'content': '本文介绍如何通过 OpenAI 兼容接口调用大模型，配置 API Key、Base URL、模型名称和错误兜底策略。',
    },
    {
        'title': 'RAG 检索增强生成：让大模型基于资料回答',
        'tags': 'RAG,大模型,检索,问答',
        'category': '人工智能',
        'content': '本文介绍 RAG 的基本流程：用户问题、文档检索、相关性排序、提示词构造和答案生成。',
    },
    {
        'title': 'TF-IDF 文本检索与文章可信度评分',
        'tags': 'TF-IDF,文本检索,可信度',
        'category': '人工智能',
        'content': '本文讲解如何使用 TF-IDF 计算用户问题和文章之间的相关性，并把相关性转换为文章可信度。',
    },
    {
        'title': 'Agent 智能体设计：意图、技能与调度',
        'tags': 'Agent,Skills,调度,AI',
        'category': '系统架构',
        'content': '本文介绍智能体系统如何根据用户意图调用不同技能，包括文章查询、推荐、算法解释和反馈记录。',
    },
    {
        'title': '用户画像系统：从对话记录到个性化推荐',
        'tags': '用户画像,推荐系统,个性化',
        'category': '系统架构',
        'content': '本文介绍如何根据用户历史问题、意图分布、反馈满意度和兴趣标签构建用户画像。',
    },
    {
        'title': '数据库设计原则：表结构、索引与范式',
        'tags': '数据库,SQL,设计',
        'category': '后端开发',
        'content': '本文讲解数据库表设计、主键、外键、索引、范式和反范式，帮助构建稳定的后端系统。',
    },
    {
        'title': 'PostgreSQL 部署实践：从 SQLite 到线上数据库',
        'tags': 'PostgreSQL,部署,数据库',
        'category': '后端开发',
        'content': '本文介绍为什么线上项目应使用 PostgreSQL，以及如何通过 DATABASE_URL 配置 Django 数据库。',
    },
    {
        'title': 'Render 部署 Django 项目完整流程',
        'tags': 'Render,Django,部署,上线',
        'category': '工程化部署',
        'content': '本文介绍如何把 Django 项目推送到 GitHub，并通过 Render Web Service 完成构建、迁移和上线。',
    },
    {
        'title': 'Django 静态文件部署：WhiteNoise 与 collectstatic',
        'tags': 'Django,静态文件,WhiteNoise,部署',
        'category': '工程化部署',
        'content': '本文讲解 Django 生产环境静态文件处理，包括 STATIC_ROOT、collectstatic 和 WhiteNoise 中间件。',
    },
    {
        'title': '软件工程化：测试、配置、日志与部署文档',
        'tags': '工程化,测试,配置,部署',
        'category': '工程化部署',
        'content': '本文总结项目工程化落地要点，包括自动化测试、环境变量配置、部署文档、接口说明和日志记录。',
    },
    {
        'title': '智能博客系统演示指南：老师汇报版',
        'tags': '项目汇报,演示,智能博客,NLP',
        'category': '项目说明',
        'content': '本文面向课程汇报，介绍智能博客系统的核心功能：大模型意图理解、V4 NLP 兜底、文章推荐、用户画像和部署上线。',
    },
]


def create_demo_user():
    user, _ = User.objects.get_or_create(username=DEMO_USERNAME)
    user.set_password(DEMO_PASSWORD)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    return user


def create_articles():
    created = 0
    for article in ARTICLES:
        _, was_created = Post.objects.update_or_create(
            title=article['title'],
            defaults={
                'content': article['content'],
                'tags': article['tags'],
                'category': article['category'],
            },
        )
        if was_created:
            created += 1
    return created


def create_demo_logs(user):
    samples = [
        ('我想学机器学习，有没有适合入门的文章', '文章推荐', 0.91),
        ('这个项目怎么部署到 Render', '项目咨询', 0.88),
        ('意图识别算法是什么', '算法咨询', 0.93),
        ('帮我找 Django 登录注册的内容', '文章查询', 0.86),
        ('你是谁', '身份介绍', 0.95),
    ]
    for user_input, intent, confidence in samples:
        ChatLog.objects.get_or_create(
            user=user,
            user_input=user_input,
            defaults={
                'predicted_intent': intent,
                'confidence': confidence,
                'algorithm': 'mock-demo',
                'response_text': '演示数据：系统已记录本次用户意图。',
                'is_helpful': True,
            },
        )


if __name__ == '__main__':
    demo_user = create_demo_user()
    created_count = create_articles()
    create_demo_logs(demo_user)
    rebuild_index()
    print(f'Demo user ready: {DEMO_USERNAME} / {DEMO_PASSWORD}')
    print(f'Mock articles ready: {len(ARTICLES)} total, {created_count} newly created')
