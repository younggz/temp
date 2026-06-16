"""
创建初始博客文章数据
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')
django.setup()

from blog.models import Post

# 清除现有数据
Post.objects.all().delete()

# 创建示例文章
articles = [
    {
        'title': 'Python入门教程',
        'tags': 'Python,入门,编程',
        'category': '编程语言',
        'content': 'Python是一种简单易学的编程语言，适合初学者入门。本文将从基础语法、数据类型、控制流等方面详细介绍Python编程。通过学习本文，你将掌握Python的基本用法，为后续学习打下坚实基础。'
    },
    {
        'title': 'Python进阶指南',
        'tags': 'Python,进阶,编程',
        'category': '编程语言',
        'content': '本文介绍Python的高级特性，包括装饰器、生成器、上下文管理器等。适合有一定Python基础的开发者深入学习，提升编程技能。'
    },
    {
        'title': 'Django框架实战',
        'tags': 'Django,Python,Web',
        'category': 'Web开发',
        'content': 'Django是一个高级Python Web框架，鼓励快速开发和简洁实用的设计。本文将通过一个完整的项目实战，教你如何使用Django构建现代化的Web应用。'
    },
    {
        'title': 'NLP自然语言处理入门',
        'tags': 'NLP,机器学习,AI',
        'category': '人工智能',
        'content': '自然语言处理（NLP）是人工智能的重要分支。本文将介绍NLP的基础概念、常用技术和实际应用，帮助你入门NLP领域。'
    },
    {
        'title': '意图识别算法详解',
        'tags': 'NLP,意图识别,算法',
        'category': '人工智能',
        'content': '意图识别是NLP中的核心任务之一。本文将详细介绍基于关键词匹配、机器学习和深度学习的意图识别方法，以及它们在实际项目中的应用。'
    },
    {
        'title': 'Agent智能代理设计模式',
        'tags': 'Agent,AI,架构',
        'category': '人工智能',
        'content': 'Agent模式是现代AI系统的核心架构。本文介绍如何设计一个可扩展的Agent系统，包括意图识别、技能调度和结果返回等关键组件。'
    },
    {
        'title': '前端开发基础',
        'tags': '前端,HTML,CSS,JavaScript',
        'category': 'Web开发',
        'content': '前端开发是Web开发的重要组成部分。本文介绍HTML、CSS和JavaScript的基础知识，帮助你快速入门前端开发。'
    },
    {
        'title': '数据库设计原理',
        'tags': '数据库,SQL,设计',
        'category': '后端开发',
        'content': '良好的数据库设计是应用性能的关键。本文介绍关系型数据库的设计原则、范式理论和实际优化技巧。'
    },
]

for article in articles:
    Post.objects.create(
        title=article['title'],
        content=article['content'],
        tags=article.get('tags', ''),
        category=article.get('category', ''),
    )

print(f'成功创建 {len(articles)} 篇示例文章！')
print('你现在可以访问系统体验智能博客功能了！')
