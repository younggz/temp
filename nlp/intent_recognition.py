"""
NLP 意图识别模块（达尔文优化版）

达尔文优化结论：
- V1 Baseline：关键词规则匹配，作为对照组
- V2 SequenceMatcher：短句模糊匹配能力较强
- V3 Jieba+Jaccard：中文分词版本，作为备选算法
- V4 Darwin Ensemble：融合 V2 与 V3，当前测评集综合最优，作为默认生产算法
"""
import jieba
import os
from django.conf import settings
from difflib import SequenceMatcher

# 加载停用词
STOP_WORDS = set()
stopwords_path = os.path.join(os.path.dirname(__file__), '..', 'stopwords.txt')
try:
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        STOP_WORDS = set([line.strip() for line in f if line.strip()])
except FileNotFoundError:
    print("⚠️ 警告: 未找到 stopwords.txt，将使用默认空停用词表")

# 定义意图类型
INTENT_QUERY_ARTICLE = '查询文章'
INTENT_LATEST_ARTICLES = '获取最新文章'
INTENT_SEARCH_ARTICLE = '搜索文章'
INTENT_HELLO = '打招呼'
INTENT_ALGORITHM_INFO = '算法咨询'
INTENT_UNKNOWN = '未知意图'

# 意图模板库
INTENT_TEMPLATES = {
    INTENT_QUERY_ARTICLE: [
        '帮我找文章',
        '查找相关的文章',
        '有没有关于的文章',
        '我想看文章',
        '搜索',
        '推荐教程',
    ],
    INTENT_LATEST_ARTICLES: [
        '最新文章',
        '最新发布的文章',
        '最近有什么新文章',
        '展示最新文章',
        '看看最近的文章',
    ],
    INTENT_SEARCH_ARTICLE: [
        '搜索文章',
        '查找文章',
        '找一下文章',
    ],
    INTENT_HELLO: [
        '你好',
        'hello',
        'hi',
        '嗨',
        '在吗',
    ],
    INTENT_ALGORITHM_INFO: [
        '有哪些算法',
        '有其他算法吗',
        '介绍一下算法',
        '算法是什么',
        '用了什么算法',
        '意图识别算法',
        '达尔文优化算法',
        'V4算法',
        '集成算法',
    ],
}


def calculate_word_similarity(text1, text2):
    """
    达尔文进化版：基于 Jieba 分词的 Jaccard 相似度
    比 SequenceMatcher 更适合中文语义匹配
    """
    # 1. 分词
    words1 = set(jieba.cut(text1))
    words2 = set(jieba.cut(text2))
    
    # 2. 过滤停用词
    words1 = words1 - STOP_WORDS
    words2 = words2 - STOP_WORDS
    
    if not words1 or not words2:
        return 0.0
        
    # 3. 计算 Jaccard 相似度: 交集 / 并集
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def calculate_sequence_similarity(text1, text2):
    """V2：SequenceMatcher 字符串相似度。"""
    return SequenceMatcher(None, text1, text2).ratio()


def extract_keyword(text):
    """
    达尔文进化版：基于停用词表的关键词提取
    """
    words = jieba.cut(text)
    # 过滤停用词和单字（通常单字无实际意义）
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    return " ".join(keywords)


def recognize_intent(user_input, algorithm=None):
    """
    识别用户输入的意图。

    Args:
        user_input: 用户自然语言输入
        algorithm: 可选算法，支持 sequence / jieba / ensemble。默认读取
            settings.NLP_INTENT_ALGORITHM，未配置时使用 ensemble。
    """
    best_intent = INTENT_UNKNOWN
    best_confidence = 0.0
    keyword = ''

    selected_algorithm = (algorithm or getattr(
        settings, 'NLP_INTENT_ALGORITHM', 'ensemble'
    )).lower()
    thresholds = {
        'sequence': getattr(settings, 'NLP_SEQUENCE_THRESHOLD', 0.32),
        'jieba': getattr(settings, 'NLP_JIEBA_THRESHOLD', 0.05),
        'ensemble': getattr(settings, 'NLP_ENSEMBLE_THRESHOLD', 0.30),
    }
    if selected_algorithm not in thresholds:
        selected_algorithm = 'ensemble'
    threshold = thresholds[selected_algorithm]
    
    # 1. 提取关键词（用于后续搜索）
    keyword = extract_keyword(user_input)

    # 规则优先：算法咨询类表达短且口语化，相似度容易被普通文章模板干扰。
    algorithm_terms = ['算法', 'v1', 'v2', 'v3', 'v4', '达尔文', '集成']
    question_terms = ['什么', '哪些', '哪个', '介绍', '解释', '其他', '吗', '怎么', '如何', '区别']
    lower_input = user_input.lower()
    if any(term in lower_input for term in algorithm_terms) and any(term in user_input for term in question_terms):
        return {
            'intent': INTENT_ALGORITHM_INFO,
            'keyword': keyword,
            'confidence': 0.88,
            'algorithm': selected_algorithm,
            'threshold': threshold,
        }
    
    # 2. 遍历模板计算相似度
    for intent, templates in INTENT_TEMPLATES.items():
        for template in templates:
            if selected_algorithm == 'jieba':
                similarity = calculate_word_similarity(user_input, template)
            elif selected_algorithm == 'sequence':
                similarity = calculate_sequence_similarity(user_input, template)
            else:
                seq_similarity = calculate_sequence_similarity(user_input, template)
                word_similarity = calculate_word_similarity(user_input, template)
                similarity = 0.7 * seq_similarity + 0.3 * word_similarity
            
            if similarity > best_confidence and similarity > threshold:
                best_confidence = similarity
                best_intent = intent
    
    # 3. 兜底逻辑：如果相似度不够，但包含强关键词，则判定为查询
    if best_intent == INTENT_UNKNOWN:
        if any(word in user_input for word in ['文章', '找', '搜索', '教程']):
            best_intent = INTENT_QUERY_ARTICLE
            best_confidence = 0.5 # 赋予中等置信度
    
    return {
        'intent': best_intent,
        'keyword': keyword,
        'confidence': best_confidence,
        'algorithm': selected_algorithm,
        'threshold': threshold,
    }
