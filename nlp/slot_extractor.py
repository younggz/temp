import jieba
import os
import re

STOP_WORDS = set()
stopwords_path = os.path.join(os.path.dirname(__file__), '..', 'stopwords.txt')
try:
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        STOP_WORDS = set([line.strip() for line in f if line.strip()])
except FileNotFoundError:
    pass


class SlotExtractor:
    def extract(self, user_input):
        slots = {
            'keyword': '',
            'tag': '',
            'count': 0,
            'category': '',
        }
        count = self._extract_count(user_input)
        if count:
            slots['count'] = count
        tag = self._extract_tag(user_input)
        if tag:
            slots['tag'] = tag
        keyword = self._extract_keyword(user_input, tag)
        if keyword:
            slots['keyword'] = keyword
        return slots

    def _extract_count(self, text):
        pattern_map = [
            (r'(\d+)篇', lambda m: int(m.group(1))),
            (r'(\d+)个', lambda m: int(m.group(1))),
            (r'几篇', lambda m: 5),
            (r'几个', lambda m: 5),
            (r'最近(\d+)篇', lambda m: int(m.group(1))),
        ]
        for pattern, func in pattern_map:
            m = re.search(pattern, text)
            if m:
                return func(m)
        return 0

    def _extract_tag(self, text):
        m = re.search(r'(?:查看|查找|搜索|筛选)?\s*([A-Za-z0-9_\-\u4e00-\u9fa5]+)\s*标签下', text)
        if m:
            tag = m.group(1).strip()
            if len(tag) > 1:
                return tag
        m = re.search(r'(?:查看|查找|搜索|筛选)?\s*([A-Za-z0-9_\-\u4e00-\u9fa5]+)\s*标签', text)
        if m:
            tag = m.group(1).strip()
            if len(tag) > 1:
                return tag
        m = re.search(r'(\S+)\s*标签', text)
        if m:
            tag = m.group(1).strip()
            if len(tag) > 1:
                return tag
        m = re.search(r'标签\s*(\S+)', text)
        if m:
            tag = m.group(1).strip()
            if len(tag) > 1:
                return tag
        m = re.search(r'(\S+)\s*分类', text)
        if m:
            tag = m.group(1).strip()
            if len(tag) > 1:
                return tag
        words = jieba.lcut(text)
        for i, w in enumerate(words):
            if w in ('标签', '分类'):
                if i > 0 and len(words[i - 1]) > 1:
                    return words[i - 1]
                if i + 1 < len(words) and len(words[i + 1]) > 1:
                    return words[i + 1]
        return ''

    def _extract_keyword(self, text, tag=''):
        stop_words = STOP_WORDS | {'文章', '帮我', '找', '推荐', '查看', '搜索',
                                    '查找', '最近', '最新', '几篇', '一些',
                                    '关于', '的', '有', '没有', '什么', '怎么',
                                    '一下', '看看', '想', '可以', '吗', '吧',
                                    '给', '我', '请', '把', '在', '了', '和',
                                    '与', '或', '是', '就', '都', '要', '会',
                                    '能', '你', '他', '她', '它', '们', '这',
                                    '那', '哪', '谁', '个', '篇', '种', '样',
                                    '来', '去', '上', '下', '到', '过'}
        words = jieba.lcut(text)
        candidates = [w for w in words
                      if w not in stop_words and len(w) > 1 and w != tag]
        return ' '.join(candidates) if candidates else ''
