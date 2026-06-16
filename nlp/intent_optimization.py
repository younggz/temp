"""
NLP 意图识别达尔文优化技能模块
==================================
基于"达尔文技能"（自然选择进化）框架，对目标算法进行对比测评与参数优化。

核心思想（达尔文进化论）：
1.  变异（Variation）：同一算法有多个版本（Baseline → SequenceMatcher → Jieba+Jaccard）
2.  选择（Selection）：通过测评指标（准确率/精确率/召回率/F1）筛选最优版本
3.  遗传（Inheritance）：最优版本的参数被保留并用于生产环境

测评指标说明：
- Accuracy（准确率）：预测正确的比例
- Precision（精确率）：预测为正类中实际为正类的比例
- Recall（召回率）：实际为正类中被正确预测的比例
- F1-Score：精确率与召回率的调和平均数
"""
import sys
import os
from typing import Dict, List, Tuple, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_blog.settings')

from nlp.evaluation import (
    DarwinEvaluator,
    BaselineRecognizer,
    SequenceMatcherRecognizer,
    JiebaRecognizer,
    DarwinEnsembleRecognizer,
    TEST_DATASET,
    INTENT_LABELS
)
from nlp.intent_recognition import recognize_intent


class IntentOptimizationSkill:
    """
    意图识别达尔文优化技能
    —— 基于达尔文技能框架，对 NLP 意图识别算法进行对比测评与优化
    
    功能：
    1. 三代算法对比测评（Baseline vs SequenceMatcher vs Jieba+Jaccard）
    2. 阈值参数扫描优化
    3. 综合优化报告生成
    """

    SKILL_NAME = "intent_optimization"
    SKILL_DESCRIPTION = "NLP意图识别达尔文优化技能 - 对目标算法进行三代对比测评与参数优化"
    SKILL_VERSION = "1.0.0"

    def __init__(self):
        self.evaluator = DarwinEvaluator(TEST_DATASET, INTENT_LABELS)

    def run_comparison(self) -> Dict[str, Any]:
        """
        运行三代算法对比测评
        
        Returns:
            {
                'baseline': { metrics... },
                'sequence_matcher': { metrics... },
                'jieba': { metrics... },
                'summary': { best_algorithm, comparison_table, ... }
            }
        """
        baseline = BaselineRecognizer()
        seq_matcher = SequenceMatcherRecognizer()
        jieba_model = JiebaRecognizer()
        ensemble_model = DarwinEnsembleRecognizer()

        res_base = self.evaluator.evaluate_model(baseline, "Baseline (关键词规则)")
        res_seq = self.evaluator.evaluate_model(seq_matcher, "V2.0 (SequenceMatcher)")
        res_jieba = self.evaluator.evaluate_model(jieba_model, "V3.0 (Jieba分词+Jaccard)")
        res_ensemble = self.evaluator.evaluate_model(ensemble_model, "V4.0 (Darwin Ensemble)")

        algorithms = {
            "Baseline (关键词规则)": {"metrics": res_base, "key": "baseline"},
            "V2.0 (SequenceMatcher)": {"metrics": res_seq, "key": "seq"},
            "V3.0 (Jieba分词+Jaccard)": {"metrics": res_jieba, "key": "jieba"},
            "V4.0 (Darwin Ensemble)": {"metrics": res_ensemble, "key": "ensemble"},
        }

        best_algo = max(algorithms.items(), key=lambda x: x[1]["metrics"]["f1"])

        table_lines = [
            f"{'指标':<15} | {'Baseline':<10} | {'V2.0 Seq':<10} | {'V3.0 Jieba':<12} | {'V4.0 Ens':<10}",
            "-" * 75,
        ]
        for metric in ['accuracy', 'precision', 'recall', 'f1']:
            table_lines.append(
                f"{metric.upper():<15} | {res_base[metric]:<10.4f} | {res_seq[metric]:<10.4f} | {res_jieba[metric]:<12.4f} | {res_ensemble[metric]:<10.4f}"
            )

        return {
            "baseline": res_base,
            "sequence_matcher": res_seq,
            "jieba": res_jieba,
            "ensemble": res_ensemble,
            "summary": {
                "best_algorithm": best_algo[0],
                "best_f1": best_algo[1]["metrics"]["f1"],
                "best_key": best_algo[1]["key"],
                "comparison_table": "\n".join(table_lines),
                "error_analysis": self._build_error_analysis(algorithms),
            },
            "success": True,
        }

    def _build_error_analysis(self, algorithms: Dict[str, Any]) -> Dict[str, Any]:
        """汇总错误样本，帮助解释算法为什么还需要继续优化。"""
        error_counts = {
            name: info["metrics"].get("error_count", 0)
            for name, info in algorithms.items()
        }
        best_name = min(error_counts.items(), key=lambda item: item[1])[0]
        representative_errors = algorithms[best_name]["metrics"].get("errors", [])[:5]
        return {
            "error_counts": error_counts,
            "best_error_algorithm": best_name,
            "representative_errors": representative_errors,
            "labels": INTENT_LABELS,
            "confusion_matrix": algorithms[best_name]["metrics"].get("confusion_matrix", []),
        }

    def threshold_scan(self) -> Dict[str, Any]:
        """
        阈值参数扫描优化
        对 Jieba+Jaccard 算法进行阈值扫描，寻找最优阈值
        
        Returns:
            {
                'threshold_results': [ {threshold, accuracy, precision, recall, f1}, ... ],
                'best_threshold': float,
                'best_f1': float,
            }
        """
        results = []
        best_threshold = 0.0
        best_f1 = 0.0

        for threshold in [round(t * 0.05, 2) for t in range(1, 11)]:
            model = self._create_threshold_model(threshold)
            metrics = self.evaluator.evaluate_model(model, f"阈值={threshold:.2f}")
            results.append({
                "threshold": threshold,
                **metrics
            })
            if metrics["f1"] > best_f1:
                best_f1 = metrics["f1"]
                best_threshold = threshold

        return {
            "threshold_results": results,
            "best_threshold": best_threshold,
            "best_f1": best_f1,
            "success": True,
        }

    def _create_threshold_model(self, threshold: float):
        """创建指定阈值的 Jieba 识别模型"""
        import jieba
        from difflib import SequenceMatcher

        class ThresholdJiebaRecognizer:
            def __init__(self, thr, stop_words, templates):
                self.thr = thr
                self.stop_words = stop_words
                self.templates = templates

            def predict(self, text: str) -> str:
                templates = {
                    "查询文章": ["帮我找文章", "查找相关的文章", "有没有关于的文章", "我想看文章", "搜索", "推荐教程"],
                    "获取最新文章": ["最新文章", "最新发布的文章", "最近有什么新文章", "展示最新文章", "看看最近的文章"],
                    "打招呼": ["你好", "hello", "hi", "嗨", "在吗"],
                    "搜索文章": ["搜索文章", "查找文章", "找一下文章"],
                }
                best_intent = "未知意图"
                best_score = 0.0
                words1 = set(jieba.cut(text)) - self.stop_words

                for intent, tpls in templates.items():
                    for tpl in tpls:
                        words2 = set(jieba.cut(tpl)) - self.stop_words
                        if not words1 or not words2:
                            continue
                        intersection = words1.intersection(words2)
                        union = words1.union(words2)
                        score = len(intersection) / len(union) if union else 0.0
                        if score > best_score:
                            best_score = score
                            best_intent = intent

                return best_intent if best_score > self.thr else "未知意图"

        from nlp.evaluation import STOP_WORDS
        return ThresholdJiebaRecognizer(threshold, STOP_WORDS, None)

    def get_full_optimization_report(self) -> Dict[str, Any]:
        """
        生成完整的优化报告（对比测评 + 阈值优化）
        
        Returns:
            {
                'comparison': {...},
                'threshold_scan': {...},
                'conclusion': str,
                'recommendation': str,
            }
        """
        comparison = self.run_comparison()
        threshold_info = self.threshold_scan()

        best_algo = comparison["summary"]["best_algorithm"]
        best_f1_compare = comparison["summary"]["best_f1"]
        best_thr = threshold_info["best_threshold"]
        best_thr_f1 = threshold_info["best_f1"]
        jieba_f1 = comparison["jieba"]["f1"]
        production_algorithm = best_algo
        if comparison["summary"]["best_key"] == "seq":
            production_threshold = 0.32
        elif comparison["summary"]["best_key"] == "ensemble":
            production_threshold = 0.30
        else:
            production_threshold = best_thr
        production_f1 = best_f1_compare
        ensemble_f1 = comparison["ensemble"]["f1"]
        error_analysis = comparison["summary"]["error_analysis"]

        conclusion_lines = [
            "=" * 60,
            "🧬 达尔文技能 · NLP 意图识别优化报告",
            "=" * 60,
            "",
            "📊 一、三代算法对比测评结论",
            f"   🏆 最优算法：{best_algo}",
            f"   📈 最优 F1-Score：{best_f1_compare:.4f}",
            "",
            f"   Baseline (关键词规则)    F1 = {comparison['baseline']['f1']:.4f}",
            f"   V2.0 (SequenceMatcher)   F1 = {comparison['sequence_matcher']['f1']:.4f}",
            f"   V3.0 (Jieba+Jaccard)     F1 = {comparison['jieba']['f1']:.4f}",
            f"   V4.0 (Darwin Ensemble)   F1 = {ensemble_f1:.4f}",
            "",
            "📐 二、阈值参数优化结论",
            f"   最优阈值: {best_thr:.2f}",
            f"   优化前 F1: {jieba_f1:.4f} (默认阈值 0.25)",
            f"   优化后 F1: {best_thr_f1:.4f} (阈值 {best_thr:.2f})",
            f"   {'✅ 阈值优化有效提升' if best_thr_f1 > jieba_f1 else 'ℹ️ 当前阈值已接近最优'}",
            "",
            "💡 三、推荐配置",
            f"   生产默认算法：{production_algorithm}",
            f"   生产阈值：{production_threshold:.2f}",
            f"   预期 F1：{production_f1:.4f}",
            f"   备选算法：V3.0 (Jieba+Jaccard)，最优阈值 {best_thr:.2f}，F1 = {best_thr_f1:.4f}",
            f"   集成算法：V4.0 (Darwin Ensemble)，F1 = {ensemble_f1:.4f}",
            "",
            "🧾 四、错误样本分析",
            f"   错误数最少算法：{error_analysis['best_error_algorithm']}",
            f"   错误数：{error_analysis['error_counts']}",
            "",
            "=" * 60,
        ]

        recommendation = (
            f"推荐生产使用「{production_algorithm}」算法，阈值设为 {production_threshold:.2f}，"
            f"预期 F1-Score 为 {production_f1:.4f}；"
            f"V3.0 (Jieba+Jaccard) 可作为备选，阈值建议 {best_thr:.2f}。"
        )

        return {
            "comparison": comparison,
            "threshold_scan": threshold_info,
            "conclusion": "\n".join(conclusion_lines),
            "recommendation": recommendation,
            "success": True,
        }

    def execute(self, action: str = "full_report", **kwargs) -> Dict[str, Any]:
        """
        执行优化技能（统一的调用入口）
        
        Args:
            action: 执行动作
                - "comparison": 仅运行对比测评
                - "threshold_scan": 仅运行阈值扫描
                - "full_report": 完整优化报告（默认）
        
        Returns:
            优化结果字典
        """
        if action == "comparison":
            return self.run_comparison()
        elif action == "threshold_scan":
            return self.threshold_scan()
        else:
            return self.get_full_optimization_report()


def run_optimization(action: str = "full_report") -> Dict[str, Any]:
    """
    便捷接口：创建优化技能并执行
    
    Args:
        action: "comparison" | "threshold_scan" | "full_report"
    
    Returns:
        优化结果
    """
    skill = IntentOptimizationSkill()
    return skill.execute(action)


def print_report(action: str = "full_report"):
    """在终端打印优化报告"""
    import django
    django.setup()
    
    result = run_optimization(action)
    if action == "full_report":
        print(result["conclusion"])
    elif action == "comparison":
        print(result["summary"]["comparison_table"])
    elif action == "threshold_scan":
        print(f"\n📐 阈值扫描结果:")
        print(f"{'阈值':<8} | {'准确率':<8} | {'精确率':<8} | {'召回率':<8} | {'F1':<8}")
        print("-" * 45)
        for row in result["threshold_results"]:
            print(f"{row['threshold']:<8.2f} | {row['accuracy']:<8.4f} | {row['precision']:<8.4f} | {row['recall']:<8.4f} | {row['f1']:<8.4f}")
        print(f"\n🏆 最优阈值: {result['best_threshold']:.2f} (F1={result['best_f1']:.4f})")


if __name__ == "__main__":
    print_report("full_report")
