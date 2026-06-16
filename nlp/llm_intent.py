import json
import os
import re
import urllib.error
import urllib.request

from django.conf import settings


class LLMIntentAnalyzer:
    """OpenAI-compatible LLM intent analyzer with safe local fallback behavior."""

    INTENTS = {
        'article_search',
        'article_recommendation',
        'identity',
        'algorithm_consulting',
        'project_consulting',
        'feedback',
        'help',
        'chat',
        'unknown',
    }

    INTENT_LABELS = {
        'article_search': '文章查询',
        'article_recommendation': '文章推荐',
        'identity': '身份介绍',
        'algorithm_consulting': '算法咨询',
        'project_consulting': '项目咨询',
        'feedback': '用户反馈',
        'help': '帮助引导',
        'chat': '闲聊',
        'unknown': '未知意图',
    }

    def __init__(self):
        self.enabled = getattr(settings, 'LLM_ENABLED', True)
        self.api_key = getattr(settings, 'LLM_API_KEY', '') or os.getenv('LLM_API_KEY', '')
        self.base_url = getattr(settings, 'LLM_BASE_URL', 'https://www.vivaapi.cn/v1').rstrip('/')
        self.model = getattr(settings, 'LLM_MODEL', 'gpt-4o-mini')
        self.timeout = getattr(settings, 'LLM_TIMEOUT', 8)

    def available(self):
        return bool(self.enabled and self.api_key)

    def analyze(self, user_input, user_profile=None):
        if not self.available():
            return self._disabled_result()

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self._system_prompt()},
                {'role': 'user', 'content': self._user_prompt(user_input, user_profile or {})},
            ],
            'temperature': 0.2,
            'response_format': {'type': 'json_object'},
        }

        try:
            raw = self._post_chat_completions(payload)
            content = raw['choices'][0]['message']['content']
            parsed = self._parse_json(content)
            return self._normalize(parsed)
        except Exception as exc:
            return {
                'ok': False,
                'source': 'llm',
                'error': str(exc)[:200],
                'intent': 'unknown',
                'intent_label': '未知意图',
                'confidence': 0.0,
                'need_article': False,
                'keywords': [],
                'query': user_input,
                'user_goal': '',
                'reply': '',
                'reason': 'LLM 调用失败，已回退到本地 NLP 算法。',
            }

    def _post_chat_completions(self, payload):
        url = f'{self.base_url}/chat/completions'
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(
            url,
            data=data,
            method='POST',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f'LLM HTTP {exc.code}: {body[:200]}') from exc

    def _system_prompt(self):
        return (
            '你是一个智能博客系统的意图分析器。'
            '你的任务不是闲聊，而是把用户自然语言转成结构化 JSON。'
            '只能输出 JSON，不要输出 Markdown。'
            '可选 intent: article_search, article_recommendation, identity, '
            'algorithm_consulting, project_consulting, feedback, help, chat, unknown。'
            '如果用户想找文章、资料、教程、学习内容，need_article=true。'
            '如果用户问你是谁，intent=identity 且 need_article=false。'
            '如果用户问项目、部署、工程化、老师汇报，intent=project_consulting。'
            '如果用户问 NLP、意图识别、V1/V2/V3/V4、达尔文优化，intent=algorithm_consulting。'
            '输出字段必须包含: intent, confidence, need_article, keywords, query, '
            'user_goal, reply_style, reason, direct_reply。'
        )

    def _user_prompt(self, user_input, user_profile):
        return json.dumps({
            'user_input': user_input,
            'known_user_profile': user_profile,
            'output_schema': {
                'intent': 'string',
                'confidence': 'number 0-1',
                'need_article': 'boolean',
                'keywords': ['string'],
                'query': 'string',
                'user_goal': 'string',
                'reply_style': 'string',
                'reason': 'string',
                'direct_reply': 'string for non-article questions',
            },
        }, ensure_ascii=False)

    def _parse_json(self, content):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', content, re.S)
            if not match:
                raise
            return json.loads(match.group(0))

    def _normalize(self, data):
        intent = str(data.get('intent', 'unknown')).strip()
        if intent not in self.INTENTS:
            intent = 'unknown'

        confidence = data.get('confidence', 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(confidence, 1.0))

        keywords = data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [keywords]
        keywords = [str(item).strip() for item in keywords if str(item).strip()]

        return {
            'ok': True,
            'source': 'llm',
            'intent': intent,
            'intent_label': self.INTENT_LABELS[intent],
            'confidence': confidence,
            'need_article': bool(data.get('need_article', False)),
            'keywords': keywords[:8],
            'query': str(data.get('query', '')).strip(),
            'user_goal': str(data.get('user_goal', '')).strip(),
            'reply_style': str(data.get('reply_style', '简洁')).strip(),
            'reason': str(data.get('reason', '')).strip(),
            'direct_reply': str(data.get('direct_reply', '')).strip(),
        }

    def _disabled_result(self):
        return {
            'ok': False,
            'source': 'llm',
            'error': 'LLM_API_KEY is not configured',
            'intent': 'unknown',
            'intent_label': '未知意图',
            'confidence': 0.0,
            'need_article': False,
            'keywords': [],
            'query': '',
            'user_goal': '',
            'reply': '',
            'reason': '未配置大模型密钥，使用本地 NLP 算法。',
        }
