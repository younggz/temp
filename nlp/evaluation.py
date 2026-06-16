"""
NLP 意图识别测评模块（达尔文进化版）
对比：Baseline -> SequenceMatcher -> Jieba分词
"""
import jieba
import os
from difflib import SequenceMatcher
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
import numpy as np

# 加载停用词
STOP_WORDS = set()
try:
    with open('stopwords.txt', 'r', encoding='utf-8') as f:
        STOP_WORDS = set([line.strip() for line in f if line.strip()])
except:
    pass

# 📊 真实测评数据集
TEST_DATASET = [
    ("帮我找Python文章", "查询文章"),
    ("查找关于Django的文章", "查询文章"),
    ("有没有Java相关的文章", "查询文章"),
    ("我想看机器学习的内容", "查询文章"),
    ("搜索NLP技术", "查询文章"),
    ("推荐一些前端教程", "查询文章"),
    ("最新文章", "获取最新文章"),
    ("最新发布的文章", "获取最新文章"),
    ("最近有什么新文章", "获取最新文章"),
    ("展示最新动态", "获取最新文章"),
    ("看看最近的文章", "获取最新文章"),
    ("你好", "打招呼"),
    ("hello", "打招呼"),
    ("hi", "打招呼"),
    ("嗨", "打招呼"),
    ("在吗", "打招呼"),
    ("搜索文章", "搜索文章"),
    ("查找文章", "搜索文章"),
    ("找一下文章", "搜索文章"),
    ("今天天气怎么样", "未知意图"),
    ("帮我写代码", "未知意图"),
    ("数据库怎么优化", "查询文章"),
    ("推荐一些Python教程", "查询文章"),
    ("看看最近的文章", "获取最新文章"),
    ("有其他算法吗", "算法咨询"),
    ("这个项目用了什么算法", "算法咨询"),
    ("介绍一下达尔文优化算法", "算法咨询"),
    ("V4集成算法是什么", "算法咨询"),
]

INTENT_LABELS = ["查询文章", "获取最新文章", "搜索文章", "打招呼", "算法咨询", "未知意图"]


class BaselineRecognizer:
    """Baseline：纯关键词规则匹配"""
    def predict_with_confidence(self, text: str) -> tuple:
        intent = self.predict(text)
        return intent, 1.0 if intent != "未知意图" else 0.0

    def predict(self, text: str) -> str:
        rules = {
            "查询文章": ["找", "文章", "搜索", "看", "有没有", "推荐"],
            "获取最新文章": ["最新", "最近", "新文章", "最新动态"],
            "打招呼": ["你好", "hello", "hi", "嗨", "在吗"],
            "算法咨询": ["算法", "达尔文", "V4", "集成"],
            "搜索文章": ["搜索文章", "查找文章"],
        }
        for intent, keywords in rules.items():
            if any(kw in text for kw in keywords):
                return intent
        return "未知意图"


class SequenceMatcherRecognizer:
    """旧版优化：SequenceMatcher 相似度"""
    templates = {
        "查询文章": ["帮我找文章", "查找相关的文章", "有没有关于的文章", "我想看文章", "搜索", "推荐教程"],
        "获取最新文章": ["最新文章", "最新发布的文章", "最近有什么新文章", "展示最新文章", "看看最近的文章"],
        "打招呼": ["你好", "hello", "hi", "嗨", "在吗"],
        "算法咨询": ["有哪些算法", "有其他算法吗", "介绍一下算法", "算法是什么", "用了什么算法", "意图识别算法", "达尔文优化算法", "V4算法", "集成算法"],
        "搜索文章": ["搜索文章", "查找文章", "找一下文章"],
    }

    threshold = 0.32

    def predict(self, text: str) -> str:
        intent, _ = self.predict_with_confidence(text)
        return intent

    def predict_with_confidence(self, text: str) -> tuple:
        best_intent = "未知意图"
        best_score = 0.0
        for intent, tpls in self.templates.items():
            for tpl in tpls:
                score = SequenceMatcher(None, text, tpl).ratio()
                if score > best_score:
                    best_score = score
                    best_intent = intent
        return (best_intent, best_score) if best_score > self.threshold else ("未知意图", best_score)


class JiebaRecognizer:
    """新版进化：Jieba 分词 + Jaccard 相似度"""
    templates = {
        "查询文章": ["帮我找文章", "查找相关的文章", "有没有关于的文章", "我想看文章", "搜索", "推荐教程"],
        "获取最新文章": ["最新文章", "最新发布的文章", "最近有什么新文章", "展示最新文章", "看看最近的文章"],
        "打招呼": ["你好", "hello", "hi", "嗨", "在吗"],
        "搜索文章": ["搜索文章", "查找文章", "找一下文章"],
    }

    def __init__(self, threshold: float = 0.25):
        self.threshold = threshold

    def predict(self, text: str) -> str:
        intent, _ = self.predict_with_confidence(text)
        return intent

    def predict_with_confidence(self, text: str) -> tuple:
        best_intent = "未知意图"
        best_score = 0.0
        
        words1 = set(jieba.cut(text)) - STOP_WORDS
        
        for intent, tpls in self.templates.items():
            for tpl in tpls:
                words2 = set(jieba.cut(tpl)) - STOP_WORDS
                if not words1 or not words2:
                    continue
                intersection = words1.intersection(words2)
                union = words1.union(words2)
                score = len(intersection) / len(union) if union else 0.0
                
                if score > best_score:
                    best_score = score
                    best_intent = intent
                    
        return (best_intent, best_score) if best_score > self.threshold else ("未知意图", best_score)


class DarwinEnsembleRecognizer:
    """
    V4：达尔文集成算法

    不是简单替换某个单算法，而是将 V2 的字符串相似度和 V3 的中文分词相似度
    做加权融合。这样既保留 SequenceMatcher 对短句模糊匹配的优势，也吸收
    Jieba+Jaccard 对中文关键词单元的敏感性。
    """

    def __init__(self, sequence_weight: float = 0.7, jieba_weight: float = 0.3, threshold: float = 0.30):
        self.sequence_weight = sequence_weight
        self.jieba_weight = jieba_weight
        self.threshold = threshold
        self.sequence = SequenceMatcherRecognizer()
        self.jieba = JiebaRecognizer(threshold=0.05)
        self.templates = SequenceMatcherRecognizer.templates

    def predict(self, text: str) -> str:
        intent, _ = self.predict_with_confidence(text)
        return intent

    def predict_with_confidence(self, text: str) -> tuple:
        best_intent = "未知意图"
        best_score = 0.0
        words1 = set(jieba.cut(text)) - STOP_WORDS

        for intent, tpls in self.templates.items():
            for tpl in tpls:
                seq_score = SequenceMatcher(None, text, tpl).ratio()

                words2 = set(jieba.cut(tpl)) - STOP_WORDS
                if words1 and words2:
                    intersection = words1.intersection(words2)
                    union = words1.union(words2)
                    jieba_score = len(intersection) / len(union) if union else 0.0
                else:
                    jieba_score = 0.0

                score = self.sequence_weight * seq_score + self.jieba_weight * jieba_score
                if score > best_score:
                    best_score = score
                    best_intent = intent

        return (best_intent, best_score) if best_score > self.threshold else ("未知意图", best_score)


class DarwinEvaluator:
    """达尔文测评器"""
    def __init__(self, dataset, labels):
        self.dataset = dataset
        self.labels = labels

    def _get_predictions(self, model):
        return [model.predict(text) for text, _ in self.dataset]

    def _get_ground_truth(self):
        return [label for _, label in self.dataset]

    def evaluate_model(self, model, name: str) -> dict:
        y_true = self._get_ground_truth()
        y_pred = self._get_predictions(model)

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, labels=self.labels, average='macro', zero_division=0)
        rec = recall_score(y_true, y_pred, labels=self.labels, average='macro', zero_division=0)
        f1 = f1_score(y_true, y_pred, labels=self.labels, average='macro', zero_division=0)

        print(f"\n{'='*50}")
        print(f"📊 {name} 测评结果")
        print(f"{'='*50}")
        print(f"✅ 准确率 (Accuracy) : {acc:.4f}")
        print(f"🎯 精确率 (Precision): {prec:.4f}")
        print(f"📥 召回率 (Recall)   : {rec:.4f}")
        print(f"⚖️  F1值 (F1-Score)  : {f1:.4f}")
        
        errors = self.get_error_cases(model)
        matrix = confusion_matrix(y_true, y_pred, labels=self.labels).tolist()

        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "errors": errors,
            "error_count": len(errors),
            "confusion_matrix": matrix,
            "labels": self.labels,
        }

    def get_error_cases(self, model) -> list:
        """返回错误样本，方便做可解释的优化分析。"""
        errors = []
        for text, expected in self.dataset:
            predicted = model.predict(text)
            if predicted != expected:
                confidence = None
                if hasattr(model, "predict_with_confidence"):
                    _, confidence = model.predict_with_confidence(text)
                errors.append({
                    "text": text,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": round(confidence, 4) if confidence is not None else None,
                })
        return errors

    def run_comparison(self):
        print("\n🧬 开始达尔文技能三代对比测评...")
        baseline = BaselineRecognizer()
        seq_matcher = SequenceMatcherRecognizer()
        jieba_model = JiebaRecognizer()
        ensemble_model = DarwinEnsembleRecognizer()

        res_base = self.evaluate_model(baseline, "Baseline (关键词规则)")
        res_seq = self.evaluate_model(seq_matcher, "V2.0 (SequenceMatcher)")
        res_jieba = self.evaluate_model(jieba_model, "V3.0 (Jieba分词+Jaccard)")
        res_ensemble = self.evaluate_model(ensemble_model, "V4.0 (Darwin Ensemble)")

        print(f"\n📈 三代算法指标对比总结:")
        print(f"{'指标':<15} | {'Baseline':<10} | {'V2.0 Seq':<10} | {'V3.0 Jieba':<12} | {'V4.0 Ens':<10}")
        print("-" * 75)
        for metric in ['accuracy', 'precision', 'recall', 'f1']:
            print(f"{metric.upper():<15} | {res_base[metric]:<10.4f} | {res_seq[metric]:<10.4f} | {res_jieba[metric]:<12.4f} | {res_ensemble[metric]:<10.4f}")
        
        return res_base, res_seq, res_jieba, res_ensemble
