import io
import logging
from typing import Dict, Any

try:
	import PyPDF2
	from pypdf import PdfReader
except ImportError:
	PyPDF2 = None
	PdfReader = None

class PDFParsingError(Exception):
	pass

def parse_pdf(content: str, decode_content) -> Dict[str, Any]:
	"""Parse PDF content and extract text, metadata."""
	if not PyPDF2 and not PdfReader:
		raise PDFParsingError("PDF parsing libraries not available")
	try:
		pdf_bytes = decode_content(content)
		pdf_file = io.BytesIO(pdf_bytes)
		text = ""
		if PdfReader:
			reader = PdfReader(pdf_file)
			for page in reader.pages:
				text += page.extract_text() or ""
		elif PyPDF2:
			reader = PyPDF2.PdfReader(pdf_file)
			for page in reader.pages:
				text += page.extract_text() or ""
		return {"text_content": text, "page_count": len(reader.pages)}
	except Exception as e:
		raise PDFParsingError(f"Failed to parse PDF: {str(e)}")
