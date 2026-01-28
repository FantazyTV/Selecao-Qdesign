import unittest
from agent.tools import feature_mapper

class TestFeatureMapper(unittest.TestCase):
    def test_map_score_explanation_to_features(self):
        qdrant_result = {"score_explanation": {"top_dimensions": [{"dimension": 1, "contribution": 0.5}]}}
        features = feature_mapper.map_score_explanation_to_features(qdrant_result)
        self.assertIsInstance(features, list)
        self.assertTrue(all(len(f) == 3 for f in features))

if __name__ == "__main__":
    unittest.main()
