import unittest
from agent.tools import edge_creator
from graph.graph_objects import Edge

class TestEdgeCreator(unittest.TestCase):
    def test_create_edge_with_evidence(self):
        evidence = [("feature1", 1, 0.5), ("feature2", 2, 0.3)]
        provenance = {"collection": "test", "id": "abc"}
        edge = edge_creator.create_edge_with_evidence("n1", "n2", 0.8, evidence, provenance)
        print(edge)
        self.assertIsInstance(edge, Edge)
        self.assertEqual(edge.from_id, "n1")
        self.assertEqual(edge.to_id, "n2")
        self.assertEqual(edge.type, "similarity")
        self.assertIn("evidence", edge.__dict__)

if __name__ == "__main__":
    unittest.main()
