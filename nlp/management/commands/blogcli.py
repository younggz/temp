import sys
from django.core.management.base import BaseCommand
from nlp.engine import NLPEngine


class Command(BaseCommand):
    help = 'NLP 智能博客 CLI - 通过自然语言查询博客内容'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            nargs='?',
            default='ask',
            help='操作类型: ask (默认)',
        )
        parser.add_argument(
            'query',
            nargs='*',
            help='自然语言查询内容',
        )

    def handle(self, *args, **kwargs):
        action = kwargs['action']
        query_parts = kwargs['query']

        if action != 'ask':
            self.stderr.write(self.style.ERROR(f'未知操作: {action}'))
            sys.exit(1)

        if not query_parts:
            self.stderr.write(self.style.WARNING(
                '请输入查询内容。\n'
                '用法: python manage.py blogcli ask "你的自然语言请求"\n\n'
                '示例:\n'
                '  python manage.py blogcli ask "帮我找 Python 入门文章"\n'
                '  python manage.py blogcli ask "推荐最新机器学习博客"\n'
                '  python manage.py blogcli ask "查看 Django 标签下的文章"\n'
                '  python manage.py blogcli ask "你好，你是谁"'
            ))
            sys.exit(1)

        user_input = ' '.join(query_parts)
        engine = NLPEngine()
        result = engine.process(user_input)

        self.stdout.write('=' * 56)
        self.stdout.write('  NLP 意图识别结果')
        self.stdout.write('=' * 56)
        self.stdout.write(f'  输入: {user_input}')
        self.stdout.write(f'  意图: {result["intent"]}')
        self.stdout.write(f'  算法: {result.get("algorithm", "-")}')
        self.stdout.write(f'  置信度: {result["confidence"]:.2%}')
        self.stdout.write(f'  槽位: {result["slots"]}')
        qa_result = result.get('qa_result')
        if qa_result:
            self.stdout.write(f'  文章可信度: {qa_result["overall_confidence"]:.2%}')
            self.stdout.write(f'  文章结果数: {qa_result["total"]}')
        self.stdout.write('=' * 56)
        self.stdout.write('')
        self.stdout.write(result['response'])
        self.stdout.write('')
        self.stdout.write('=' * 56)
