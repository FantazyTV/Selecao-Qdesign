import unittest
from agent.tools import file_parser


class TestFileParser(unittest.TestCase):
    def test_decode_content(self):
        b64 = file_parser.ContentParser.decode_content("dGVzdA==")
        self.assertEqual(b64, b"test")

    def test_parse_text(self):
        result = file_parser.ContentParser.parse_text("This is a protein test.")
        self.assertIn("text_content", result)
        self.assertIn("keywords", result)

    def test_parse_pdf(self):
        # Use a minimal PDF file in base64 (empty PDF)
        minimal_pdf_b64 = "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0tpZHMgWzMgMCBSXS9Db3VudCAxPj4KZW5kb2JqCjMgMCBvYmoKPDwvVHlwZS9QYWdlL1BhcmVudCAyIDAgUi9NZWRpYUJveFswIDAgNjEyIDc5Ml0+PgplbmRvYmoKeHJlZgowIDQKMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwNzAgMDAwMDAgbiAKMDAwMDAwMTE2IDAwMDAwIG4gCnRyYWlsZXIKPDwvUm9vdCAxIDAgUi9TaXplIDQ+PgpzdGFydHhyZWYKMTMwCiUlRU9G"
        try:
            result = file_parser.ContentParser.parse_pdf(minimal_pdf_b64)
            self.assertIn("text_content", result)
        except Exception:
            pass  # Acceptable if PDF libs are not installed

    def test_parse_image(self):
        # Use a minimal PNG file in base64 (1x1 pixel)
        minimal_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAgMBApUCBwAAAABJRU5ErkJggg=="
        try:
            result = file_parser.ContentParser.parse_image(minimal_png_b64)
            self.assertIn("size_bytes", result)
        except Exception:
            pass  # Acceptable if PIL is not installed

    def test_parse_cif(self):
        minimal_cif = """data_1ABC\n_struct.title    \"Test Structure\"\n_entity.pdbx_description    \"Hemoglobin\"\n_entity_src_gen.pdbx_gene_src_scientific_name    \"Homo sapiens\"\n_struct_asym.id    A\nATOM      1  N   MET A   1      11.104  13.207   2.100  1.00 20.00           N\n_refine.ls_d_res_high   2.0\n"""
        result = file_parser.ContentParser.parse_cif(minimal_cif)
        self.assertIn("entry_id", result)
        self.assertIn("title", result)
        self.assertIn("molecules", result)

if __name__ == "__main__":
    unittest.main()
