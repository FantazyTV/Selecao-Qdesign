import unittest
import logging
import numpy as np
from agent.tools import vector_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retrieval_tests")

class TestVectorSearch(unittest.TestCase):
    def setUp(self):
        self.seed_vector = np.random.rand(1280).tolist()

    def test_retrieve_similar_cif(self):
        logger.info("Testing retrieve_similar_cif with dummy vector...")
        try:
            results = vector_search.retrieve_similar_cif(self.seed_vector, n=2)
            logger.info(f"CIF Results: {results}")
            self.assertIsInstance(results, list)
        except Exception as e:
            logger.error(f"retrieve_similar_cif failed: {e}")
            self.fail(str(e))

    def test_retrieve_similar_fasta(self):
        logger.info("Testing retrieve_similar_fasta with dummy vector...")
        try:
            results = vector_search.retrieve_similar_fasta(self.seed_vector, n=2)
            logger.info(f"FASTA Results: {results}")
            self.assertIsInstance(results, list)
        except Exception as e:
            logger.error(f"retrieve_similar_fasta failed: {e}")
            self.fail(str(e))

if __name__ == "__main__":
    unittest.main()
