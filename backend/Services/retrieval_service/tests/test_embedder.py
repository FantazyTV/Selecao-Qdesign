import unittest
from agent.tools import embedder
from graph.graph_objects import Node

class TestEmbedder(unittest.TestCase):
    def test_dummy_embedder(self):
        vec = embedder.dummy_embedder("test")
        self.assertEqual(len(vec), 1280)
        self.assertTrue(all(isinstance(x, float) for x in vec))
    def test_embed_if_missing(self):
        node = Node(id="n1", label="test", metadata={}, embedding=None)
        vec = embedder.embed_if_missing(node, embedder.dummy_embedder)
        self.assertEqual(len(vec), 1280)
        self.assertIs(node.embedding, vec)

if __name__ == "__main__":
    unittest.main()
