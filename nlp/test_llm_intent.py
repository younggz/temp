from unittest.mock import patch

from django.test import TestCase

from blog.models import Post
from nlp.engine import NLPEngine
from nlp.relevance import rebuild_index


class LLMEnhancedIntentTests(TestCase):
    def test_llm_identity_intent_takes_over_when_confident(self):
        with patch('nlp.llm_intent.LLMIntentAnalyzer.analyze') as mocked:
            mocked.return_value = {
                'ok': True,
                'source': 'llm',
                'intent': 'identity',
                'intent_label': '身份介绍',
                'confidence': 0.91,
                'need_article': False,
                'keywords': [],
                'query': '',
                'user_goal': '',
                'reply_style': '简洁',
                'reason': '用户在询问助手身份',
                'direct_reply': '我是智能博客助手。',
            }

            result = NLPEngine().process('你是谁')

        self.assertEqual(result['routing_source'], 'llm')
        self.assertEqual(result['intent'], '身份介绍')
        self.assertEqual(result['response'], '我是智能博客助手。')
        self.assertEqual(result['algorithm'], 'llm+v4_fallback')

    def test_llm_article_need_searches_article_database(self):
        Post.objects.create(
            title='机器学习入门指南',
            tags='机器学习,入门,AI',
            category='人工智能',
            content='机器学习入门需要理解监督学习、无监督学习、模型训练和评估方法。',
        )
        rebuild_index()

        with patch('nlp.llm_intent.LLMIntentAnalyzer.analyze') as mocked:
            mocked.return_value = {
                'ok': True,
                'source': 'llm',
                'intent': 'article_recommendation',
                'intent_label': '文章推荐',
                'confidence': 0.88,
                'need_article': True,
                'keywords': ['机器学习', '入门'],
                'query': '机器学习 入门',
                'user_goal': '学习机器学习入门内容',
                'reply_style': '教学式',
                'reason': '用户想找学习文章',
                'direct_reply': '',
            }

            result = NLPEngine().process('我想学机器学习，给我适合入门的文章')

        self.assertEqual(result['routing_source'], 'llm')
        self.assertEqual(result['intent'], '文章推荐')
        self.assertIsNotNone(result['qa_result'])
        self.assertTrue(result['qa_result']['found'])
        self.assertIn('机器学习入门指南', result['response'])
