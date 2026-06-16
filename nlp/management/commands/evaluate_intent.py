"""
Django 管理命令：python manage.py evaluate_intent
用于在终端直接运行达尔文测评与优化
"""
from django.core.management.base import BaseCommand
from nlp.evaluation import DarwinEvaluator, TEST_DATASET, INTENT_LABELS


class Command(BaseCommand):
    help = '运行 NLP 意图识别达尔文技能对比测评（三代算法对比）'

    def handle(self, *args, **kwargs):
        evaluator = DarwinEvaluator(TEST_DATASET, INTENT_LABELS)
        
        # 运行对比测评
        res_base, res_seq, res_jieba = evaluator.run_comparison()
        
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 测评完成！\n"
            f"💡 当前真实测评集上，V2.0 (SequenceMatcher) 的 F1-Score 最佳。\n"
            f"🚀 建议生产默认使用 V2.0，并保留 V3.0 (Jieba+Jaccard) 作为备选算法。"
        ))
