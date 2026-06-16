import io
from contextlib import redirect_stdout

from django.test import TestCase, override_settings

from blog.models import Post
from nlp.evaluation import (
    BaselineRecognizer,
    DarwinEnsembleRecognizer,
    DarwinEvaluator,
    INTENT_LABELS,
    JiebaRecognizer,
    SequenceMatcherRecognizer,
    TEST_DATASET,
)
from nlp.intent_optimization import IntentOptimizationSkill
from nlp.intent_recognition import recognize_intent
from nlp.engine import NLPEngine
from nlp.relevance import rebuild_index
from nlp.skills import Skills


class IntentDarwinEvaluationTests(TestCase):
    def test_sequence_matcher_is_current_best_algorithm(self):
        evaluator = DarwinEvaluator(TEST_DATASET, INTENT_LABELS)

        with redirect_stdout(io.StringIO()):
            baseline = evaluator.evaluate_model(BaselineRecognizer(), "baseline")
            sequence = evaluator.evaluate_model(SequenceMatcherRecognizer(), "sequence")
            jieba = evaluator.evaluate_model(JiebaRecognizer(), "jieba")
            ensemble = evaluator.evaluate_model(DarwinEnsembleRecognizer(), "ensemble")

        self.assertGreater(sequence["f1"], baseline["f1"])
        self.assertGreater(sequence["f1"], jieba["f1"])
        self.assertGreater(ensemble["f1"], baseline["f1"])
        self.assertGreater(ensemble["f1"], sequence["f1"])
        self.assertAlmostEqual(ensemble["f1"], 0.9556, places=4)
        self.assertIn("confusion_matrix", ensemble)
        self.assertIn("errors", ensemble)

    def test_threshold_scan_improves_jieba_backup_algorithm(self):
        skill = IntentOptimizationSkill()
        with redirect_stdout(io.StringIO()):
            scan = skill.threshold_scan()

        default_row = next(row for row in scan["threshold_results"] if row["threshold"] == 0.25)
        self.assertEqual(scan["best_threshold"], 0.05)
        self.assertGreater(scan["best_f1"], default_row["f1"])

    @override_settings(NLP_INTENT_ALGORITHM="ensemble")
    def test_production_intent_recognition_defaults_to_ensemble_family(self):
        result = recognize_intent("帮我找Python文章")

        self.assertEqual(result["intent"], "查询文章")
        self.assertEqual(result["algorithm"], "ensemble")
        self.assertGreaterEqual(result["confidence"], 0.30)

    @override_settings(NLP_INTENT_ALGORITHM="ensemble")
    def test_algorithm_question_is_recognized_as_algorithm_consulting(self):
        result = recognize_intent("有其他算法吗")

        self.assertEqual(result["intent"], "算法咨询")
        self.assertEqual(result["algorithm"], "ensemble")
        self.assertGreaterEqual(result["confidence"], 0.80)


class ArticleConfidenceTests(TestCase):
    def setUp(self):
        Post.objects.create(
            title="Python入门教程",
            tags="Python,入门,编程",
            category="编程语言",
            content="Python是一种简单易学的编程语言，适合初学者入门。",
        )
        Post.objects.create(
            title="数据库设计原理",
            tags="数据库,SQL,设计",
            category="后端开发",
            content="良好的数据库设计是应用性能的关键，包含范式理论和优化技巧。",
        )
        rebuild_index()

    def test_article_search_returns_confidence_scores(self):
        result = Skills.query_article_qa("Python怎么入门", top_k=3)

        self.assertTrue(result["found"])
        self.assertGreater(result["overall_confidence"], 0)
        self.assertEqual(result["results"][0]["title"], "Python入门教程")
        self.assertIn(result["results"][0]["confidence_label"], {"高", "中", "低"})

    def test_article_search_filters_very_low_confidence_results(self):
        result = Skills.query_article_qa("今天天气怎么样", top_k=3)

        self.assertFalse(result["found"])
        self.assertEqual(result["results"], [])
        self.assertIn("没有找到高可信相关文章", result["text_response"])
