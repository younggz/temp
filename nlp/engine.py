from nlp.freeform import FreeformInstructionAnalyzer
from nlp.intent_recognition import (
    INTENT_ALGORITHM_INFO,
    INTENT_HELLO,
    INTENT_LATEST_ARTICLES,
    INTENT_QUERY_ARTICLE,
    INTENT_SEARCH_ARTICLE,
    INTENT_UNKNOWN,
    recognize_intent,
)
from nlp.llm_intent import LLMIntentAnalyzer
from nlp.skills import Skills
from nlp.slot_extractor import SlotExtractor


SKILL_ROUTING = {
    INTENT_QUERY_ARTICLE: 'query_article',
    INTENT_LATEST_ARTICLES: 'get_latest_articles',
    INTENT_SEARCH_ARTICLE: 'search_articles',
    INTENT_HELLO: 'say_hello',
    INTENT_ALGORITHM_INFO: 'explain_algorithms',
}


class NLPEngine:
    """NLP Agent engine: intent recognition -> skill routing -> freeform fallback."""

    def __init__(self):
        self.skills = Skills()
        self.slot_extractor = SlotExtractor()
        self.freeform_analyzer = FreeformInstructionAnalyzer()
        self.llm_analyzer = LLMIntentAnalyzer()

    def process(self, user_input, intent_override=None, user_profile=None):
        llm_result = self.llm_analyzer.analyze(user_input, user_profile=user_profile)
        if not intent_override and self._should_use_llm(llm_result):
            return self._process_llm_result(user_input, llm_result)

        intent_result = recognize_intent(user_input)
        intent = intent_override or intent_result['intent']
        confidence = intent_result['confidence']
        slots = self.slot_extractor.extract(user_input)

        intent, response, qa_result, freeform_analysis = self._route_and_execute(
            intent, slots, user_input
        )

        return {
            'intent': intent,
            'slots': slots,
            'confidence': confidence,
            'algorithm': intent_result.get('algorithm', ''),
            'threshold': intent_result.get('threshold', 0),
            'response': response,
            'qa_result': qa_result,
            'freeform_analysis': freeform_analysis,
            'llm_analysis': llm_result,
            'routing_source': 'local_nlp',
        }

    def _should_use_llm(self, llm_result):
        return bool(llm_result.get('ok') and llm_result.get('confidence', 0) >= 0.55)

    def _process_llm_result(self, user_input, llm_result):
        query = llm_result.get('query') or ' '.join(llm_result.get('keywords', [])) or user_input
        intent = llm_result.get('intent_label', '未知意图')
        qa_result = None

        if llm_result.get('need_article'):
            qa_result = self.skills.query_article_qa(query=query, top_k=5, min_confidence=0.08)
            if qa_result['found']:
                response = self._build_llm_article_response(llm_result, qa_result)
            else:
                response = (
                    f"我理解你的需求是：{llm_result.get('user_goal') or query}\n\n"
                    f"但当前文章库里没有找到高相关内容。你可以换一种说法，或者补充更具体的主题。"
                )
            return self._result_from_llm(intent, llm_result, response, qa_result)

        direct_reply = llm_result.get('direct_reply') or self._default_direct_reply(llm_result)
        return self._result_from_llm(intent, llm_result, direct_reply, None)

    def _result_from_llm(self, intent, llm_result, response, qa_result):
        return {
            'intent': intent,
            'slots': {
                'keyword': ' '.join(llm_result.get('keywords', [])),
                'tag': '',
                'count': 0,
                'category': '',
            },
            'confidence': llm_result.get('confidence', 0.0),
            'algorithm': 'llm+v4_fallback',
            'threshold': 0.55,
            'response': response,
            'qa_result': qa_result,
            'freeform_analysis': None,
            'llm_analysis': llm_result,
            'routing_source': 'llm',
        }

    def _build_llm_article_response(self, llm_result, qa_result):
        goal = llm_result.get('user_goal') or llm_result.get('query') or '你的需求'
        lines = [
            f"我理解你的需求是：{goal}",
            "",
            "根据文章库检索结果，推荐这些内容：",
            "",
        ]
        for index, item in enumerate(qa_result['results'], 1):
            lines.extend([
                f"{index}. {item['title']}",
                f"   可信度：{item['confidence'] * 100:.0f}%（{item['confidence_label']}）",
                f"   推荐理由：与关键词「{'、'.join(llm_result.get('keywords', [])[:4]) or qa_result['query']}」相关。",
                f"   链接：/post/{item['id']}/",
                "",
            ])
        lines.append("你可以继续补充学习阶段、偏好的方向或文章难度，我会进一步缩小推荐范围。")
        return "\n".join(lines)

    def _default_direct_reply(self, llm_result):
        intent = llm_result.get('intent')
        if intent == 'identity':
            return (
                "我是智能博客助手，可以理解你的自然语言需求，帮你检索文章、推荐内容、"
                "解释项目算法，并记录你的意图和反馈来形成个人画像。"
            )
        if intent == 'feedback':
            return "我已经理解这是一次反馈，会把它记录为用户反馈样本，用于后续优化意图识别和推荐效果。"
        if intent in {'algorithm_consulting', 'project_consulting', 'help'}:
            return llm_result.get('reason') or "我可以继续解释项目算法、工程化结构、部署方式或用户使用流程。"
        return llm_result.get('reason') or "我已经理解你的意思，可以继续帮你分析或检索相关内容。"

    def _route_and_execute(self, intent, slots, raw_input):
        if self._is_tag_request(raw_input) and slots['tag']:
            return ('标签筛选', self.skills.filter_by_tag(tag=slots['tag']), None, None)

        skill_name = SKILL_ROUTING.get(intent, '')

        if skill_name == 'say_hello':
            return (intent, self.skills.say_hello(), None, None)

        if skill_name == 'explain_algorithms':
            return (intent, self.skills.explain_algorithms(), None, None)

        if skill_name == 'get_latest_articles':
            response = self.skills.get_latest_articles(count=slots['count'] or 5)
            return (intent, response, None, None)

        if skill_name == 'search_articles':
            return (intent, self.skills.search_articles(), None, None)

        if self._is_recommend_request(raw_input):
            keyword = slots['keyword'] or raw_input
            response = self.skills.recommend_articles(keyword=keyword, count=slots['count'] or 5)
            return ('推荐', response, None, None)

        if intent == INTENT_UNKNOWN:
            freeform_analysis = self.freeform_analyzer.analyze(raw_input)
            freeform_kind = freeform_analysis.get('kind', 'open')
            if freeform_kind in {'project', 'feedback', 'help', 'open'}:
                return ('自由指令分析', freeform_analysis['response'], None, freeform_analysis)

            qa_result = self.skills.query_article_qa(query=raw_input, top_k=slots['count'] or 5)
            if qa_result['found'] and qa_result['overall_confidence'] >= 0.65:
                return ('语义检索', qa_result['text_response'], qa_result, None)
            return ('自由指令分析', freeform_analysis['response'], None, freeform_analysis)

        keyword = slots['keyword'] or raw_input
        qa_result = self.skills.query_article_qa(query=keyword, top_k=slots['count'] or 5)
        return (intent, qa_result['text_response'], qa_result, None)

    @staticmethod
    def _is_tag_request(text):
        return any(trigger in text for trigger in ['标签', '分类', 'tag', 'Tag'])

    @staticmethod
    def _is_recommend_request(text):
        return any(trigger in text for trigger in ['推荐', '适合', '给我几篇', '看看什么'])
