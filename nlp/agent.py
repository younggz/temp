"""
Agent 调度模块（达尔文进化版）
"""
from nlp.intent_recognition import recognize_intent, INTENT_QUERY_ARTICLE, INTENT_LATEST_ARTICLES, INTENT_SEARCH_ARTICLE, INTENT_HELLO
from nlp.skills import Skills


class Agent:
    """
    智能代理（Agent）
    负责接收用户输入，识别意图，并调用相应的功能模块
    """
    
    def __init__(self):
        self.skills = Skills()
    
    def process(self, user_input):
        """原始处理方法，仅返回文本结果"""
        result = self.process_with_confidence(user_input)
        return result['response']
    
    def process_with_confidence(self, user_input):
        """
        增强版处理方法，返回包含置信度的字典
        用于达尔文反馈闭环
        """
        # 步骤1：意图识别
        intent_result = recognize_intent(user_input)
        intent = intent_result['intent']
        keyword = intent_result['keyword']
        confidence = intent_result['confidence']
        
        # 步骤2：根据意图调度相应的 Skill
        if intent == INTENT_QUERY_ARTICLE:
            result = self.skills.query_article(keyword)
        elif intent == INTENT_LATEST_ARTICLES:
            result = self.skills.get_latest_articles()
        elif intent == INTENT_SEARCH_ARTICLE:
            result = self.skills.search_articles()
        elif intent == INTENT_HELLO:
            result = self.skills.say_hello()
        else:
            result = self.skills.unknown_intent()
        
        return {
            'intent': intent,
            'keyword': keyword,
            'confidence': confidence,
            'response': result
        }
