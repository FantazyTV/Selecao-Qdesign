import unittest
import logging
from agent.agent import RetrievalAgent
from graph.graph_objects import Node

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retrieval_tests")


class TestRetrievalAgent(unittest.TestCase):
    def setUp(self):
        self.agent = RetrievalAgent()

    def test_text_only_inserts_node(self):
        text = "Increasing hymoglobin performance in cold environment"
        node_id = f"text:{text[:64]}"
        node = Node(id=node_id, type="text", label=text, metadata={"source": "test"})
        self.agent.graph.add_node(node)
        self.assertIn(node_id, self.agent.graph.nodes)

    def test_text_with_cif_inserts_node_with_file(self):
        text = "Increasing hymoglobin performance in cold environment"
        cif_path = "./data/1E2A.cif"
        node_id = "cif:1E2A"
        node = Node(id=node_id, type="cif", label="1E2A.cif", metadata={"file_path": cif_path, "text": text})
        self.agent.graph.add_node(node)
        self.assertIn(node_id, self.agent.graph.nodes)
        self.assertEqual(self.agent.graph.nodes[node_id].metadata.get("file_path"), cif_path)


if __name__ == "__main__":
    unittest.main()
