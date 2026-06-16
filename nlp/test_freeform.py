from django.test import TestCase

from nlp.engine import NLPEngine


class FreeformInstructionTests(TestCase):
    def test_unknown_instruction_returns_structured_freeform_analysis(self):
        result = NLPEngine().process("我想知道这个项目后面怎么继续完善比较好")

        self.assertEqual(result["intent"], "自由指令分析")
        self.assertIn("自由指令分析", result["response"])
        self.assertIsNotNone(result["freeform_analysis"])
        self.assertIn("action", result["freeform_analysis"])
