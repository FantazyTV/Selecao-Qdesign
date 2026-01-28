import unittest
from agent.tools import db_query

class TestDBQuery(unittest.TestCase):
    def test_resolve_protein_name(self):
        result = db_query.resolve_protein_name("hemoglobin")
        print("Resolved Protein Info:", result)
        self.assertIsInstance(result, dict)
        self.assertIn("pdb_ids", result)
        self.assertIn("uniprot_ids", result)

        result = db_query.resolve_protein_name("insulin")
        print("Resolved Protein Info:", result)

if __name__ == "__main__":
    unittest.main()
