"""
TF-IDF 相关性评分 & 可信度评估模块
===================================
对搜索结果进行语义相关性评分，输出可信度（0~1）。
用于判断"检索到的文章是否真的相关/正确"。

核心流程：
  用户查询 → Jieba分词 → TF-IDF向量化 → 余弦相似度计算
  → 归一化 → 每条结果的可信度分数

使用方法：
    scorer = RelevanceScorer()
    results = scorer.search("Python列表怎么用", top_k=5)
    # results = [(article_id, title, confidence, snippet), ...]
"""

import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Optional


class RelevanceScorer:
    """
    TF-IDF 相关性评分器
    基于 TF-IDF + 余弦相似度，计算用户查询与文章的语义相关性。
    """

    def __init__(self, max_features: int = 5000):
        """
        Args:
            max_features: TF-IDF 最大特征数（词汇表大小）
        """
        self.vectorizer = TfidfVectorizer(
            tokenizer=self._tokenize,
            max_features=max_features,
            # 增加 ngram 范围以捕获短语
            ngram_range=(1, 2),
            # 忽略单字符词
            min_df=1,
            # 平滑 IDF
            smooth_idf=True,
        )
        self._fitted = False
        self._article_vectors = None
        self._articles = []  # [(id, title, content), ...]

    def _tokenize(self, text: str) -> List[str]:
        """Jieba 中文分词，过滤停用词和单字"""
        words = jieba.lcut(text)
        # 过滤：长度 > 1 的词（滤掉标点、单字等无意义词）
        return [w for w in words if len(w) > 1]

    def build_index(self, articles: List[Tuple[int, str, str]]):
        """
        构建 TF-IDF 索引（从所有文章的内容学习）

        Args:
            articles: [(id, title, content), ...] 文章列表
        """
        if not articles:
            return

        self._articles = articles

        # 将标题和内容合并作为文档（标题权重更高，重复一次以增强）
        corpus = [f"{title} {title} {content}" for _, title, content in articles]

        # 拟合 TF-IDF 向量化器
        self._article_vectors = self.vectorizer.fit_transform(corpus)
        self._fitted = True

    def compute_relevance(
        self, query: str, top_k: int = 5
    ) -> List[dict]:
        """
        计算查询与所有文章的相关性，返回排序后的结果

        Args:
            query: 用户查询（自然语言问题/关键词）
            top_k: 返回前 k 条结果

        Returns:
            [{
                'id': article_id,
                'title': article_title,
                'confidence': float (0~1),  # 可信度分数
                'snippet': str,              # 内容摘要
            }, ...]
        """
        if not self._fitted or not self._articles:
            return []

        # 将查询向量化
        query_vec = self.vectorizer.transform([query])

        # 计算余弦相似度
        similarities = cosine_similarity(query_vec, self._article_vectors).flatten()

        # 将分数归一化到 0~1（用 min-max 归一化，避免极端值）
        score_max = similarities.max()
        score_min = similarities.min()

        if score_max > score_min:
            normalized = (similarities - score_min) / (score_max - score_min)
        elif score_max > 0:
            normalized = similarities / score_max
        else:
            normalized = similarities

        # 构建结果
        results = []
        for idx, (aid, title, content) in enumerate(self._articles):
            results.append({
                'id': aid,
                'title': title,
                'confidence': round(float(normalized[idx]), 4),
                'raw_score': round(float(similarities[idx]), 4),
                'snippet': content[:120] + ('...' if len(content) > 120 else ''),
            })

        # 按归一化分数降序排列
        results.sort(key=lambda x: x['confidence'], reverse=True)

        return results[:top_k]

    def search_with_confidence(
        self, query: str, top_k: int = 5, min_confidence: float = 0.15
    ) -> dict:
        """
        高级搜索接口：返回带可信度评估的完整结果

        Args:
            query: 用户查询
            top_k: 返回结果数
            min_confidence: 最低可信度阈值（低于此不返回）

        Returns:
            {
                'query': str,
                'total_found': int,
                'overall_confidence': float,  # 整体可信度（最高分）
                'results': [{
                    'id', 'title', 'confidence', 'snippet',
                    'confidence_label': str  # '高'/'中'/'低'
                }, ...]
            }
        """
        results = self.compute_relevance(query, top_k=top_k)

        # 过滤低可信度结果
        results = [r for r in results if r['confidence'] >= min_confidence]

        # 添加可读标签
        for r in results:
            r['confidence_label'] = self._confidence_label(r['confidence'])

        overall = results[0]['confidence'] if results else 0.0

        return {
            'query': query,
            'total_found': len(results),
            'overall_confidence': round(overall, 4),
            'results': results,
        }

    @staticmethod
    def _confidence_label(score: float) -> str:
        """将数值分数转为可读标签"""
        if score >= 0.7:
            return '高'
        elif score >= 0.4:
            return '中'
        else:
            return '低'


# ==================== 全局单例 ====================
_scorer_instance = None


def get_scorer() -> RelevanceScorer:
    """获取/初始化全局评分器单例"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = RelevanceScorer()
        # 首次使用时自动从数据库加载文章
        _auto_build_index(_scorer_instance)
    return _scorer_instance


def _auto_build_index(scorer: RelevanceScorer):
    """从 Django 数据库自动加载文章并构建索引"""
    try:
        import django
        import os

        if not os.environ.get('DJANGO_SETTINGS_MODULE'):
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')

        if not django.apps.apps.ready:
            django.setup()

        from blog.models import Post
        articles = [(p.id, p.title, p.content) for p in Post.objects.all()]
        scorer.build_index(articles)
    except Exception as e:
        print(f"[relevance] 自动加载文章失败（可忽略，稍后手动加载）: {e}")


def rebuild_index():
    """手动重建索引（在新增/修改文章后调用）"""
    global _scorer_instance
    _scorer_instance = None  # 强制重建
    return get_scorer()
