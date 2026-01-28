import unittest
import numpy as np
from agent.tools import retriever

class TestRetriever(unittest.TestCase):
    def test_retrieve_candidates(self):
        seed_vector = np.random.rand(1280).tolist()
        results = retriever.retrieve_candidates(seed_vector, n=1)
        self.assertIsInstance(results, list)

if __name__ == "__main__":
    unittest.main()
