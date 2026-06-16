import re

import jieba


class FreeformInstructionAnalyzer:
    """Analyze open-ended user instructions when fixed intent routing is not enough."""

    ACTION_RULES = [
        {
            'kind': 'search',
            'name': '文章检索',
            'triggers': ['找', '查', '搜索', '有没有', '关于', '资料', '文章', '教程', '内容'],
            'next_step': '我可以先把这句话转成文章检索，并返回相关内容和可信度。',
        },
        {
            'kind': 'recommend',
            'name': '内容推荐',
            'triggers': ['推荐', '适合', '看看', '学习', '入门', '进阶'],
            'next_step': '我可以根据关键词和你的历史高频意图推荐文章。',
        },
        {
            'kind': 'project',
            'name': '项目/算法咨询',
            'triggers': ['算法', '模型', '意图', '置信度', '达尔文', '优化', '工程化', '部署', 'agent'],
            'next_step': '我可以解释项目中的算法、工程化设计或 Agent 调度流程。',
        },
        {
            'kind': 'feedback',
            'name': '用户反馈',
            'triggers': ['不对', '错了', '没用', '不好', '看不懂', '不准确', '不是这个'],
            'next_step': '我会把这类表达记为反馈样本，后续用于优化意图识别模板和阈值。',
        },
        {
            'kind': 'help',
            'name': '帮助引导',
            'triggers': ['怎么用', '能做什么', '帮助', '使用', '功能'],
            'next_step': '我可以说明当前系统支持的查询、推荐、算法解释和用户画像能力。',
        },
    ]

    GENERIC_STOP_WORDS = {
        '我', '你', '他', '她', '它', '我们', '你们', '他们', '这个', '那个', '一下',
        '一个', '一些', '什么', '怎么', '如何', '可以', '能够', '帮我', '请', '的',
        '了', '吗', '呢', '吧', '啊', '是', '有', '和', '或者', '但是', '如果',
    }

    def analyze(self, text):
        clean_text = (text or '').strip()
        tokens = self._keywords(clean_text)
        action_scores = []

        for rule in self.ACTION_RULES:
            score = self._score_rule(clean_text, tokens, rule['triggers'])
            if score > 0:
                action_scores.append({
                    'kind': rule['kind'],
                    'name': rule['name'],
                    'score': score,
                    'next_step': rule['next_step'],
                })

        action_scores.sort(key=lambda item: item['score'], reverse=True)
        primary = action_scores[0] if action_scores else {
            'name': '开放问题分析',
            'kind': 'open',
            'score': 0.2,
            'next_step': '我会先提取关键词，并尝试转成检索或项目咨询问题。',
        }

        return {
            'action': primary['name'],
            'kind': primary.get('kind', 'open'),
            'confidence': min(primary['score'], 0.92),
            'keywords': tokens[:8],
            'candidates': action_scores[:3],
            'next_step': primary['next_step'],
            'response': self._build_response(clean_text, tokens, primary, action_scores[:3]),
        }

    def _score_rule(self, text, tokens, triggers):
        score = 0.0
        for trigger in triggers:
            if trigger in text:
                score += 0.28
            if trigger in tokens:
                score += 0.18
        return min(score, 1.0)

    def _keywords(self, text):
        raw_words = jieba.lcut(text)
        words = []
        for word in raw_words:
            word = word.strip()
            if not word or word in self.GENERIC_STOP_WORDS:
                continue
            if re.fullmatch(r'[\W_]+', word):
                continue
            if len(word) == 1 and not re.fullmatch(r'[A-Za-z0-9]', word):
                continue
            words.append(word)
        return words

    def _build_response(self, text, keywords, primary, candidates):
        keyword_text = '、'.join(keywords[:6]) if keywords else '暂无明显关键词'
        candidate_text = '、'.join([item['name'] for item in candidates]) if candidates else primary['name']
        confidence = round(min(primary['score'], 0.92) * 100)
        return (
            f"我没有把这句话强行归到固定指令，但已经做了自由指令分析：\n\n"
            f"原始输入：{text}\n"
            f"可能动作：{primary['name']}（分析置信度 {confidence}%）\n"
            f"关键词：{keyword_text}\n"
            f"候选方向：{candidate_text}\n\n"
            f"{primary['next_step']}\n"
            f"你也可以直接继续用口语描述需求，我会优先尝试检索文章、解释项目算法或记录反馈。"
        )
