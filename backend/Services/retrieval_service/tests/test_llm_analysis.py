import unittest
from agent.tools import llm_analysis

class TestLLMAnalysis(unittest.TestCase):
    def test_subllmtools_init(self):
        tool = llm_analysis.SubLLMTools()
        self.assertIsInstance(tool, llm_analysis.SubLLMTools)

if __name__ == "__main__":
    unittest.main()
