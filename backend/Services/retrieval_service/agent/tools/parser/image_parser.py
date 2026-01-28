import io
import logging
from typing import Dict, Any

try:
	from PIL import Image
	import pytesseract
except ImportError:
	Image = None
	pytesseract = None

class ImageParsingError(Exception):
	pass

def parse_image(content: str, decode_content) -> Dict[str, Any]:
	"""Parse image content and extract text via OCR if available."""
	try:
		image_bytes = decode_content(content)
		parsed_data = {
			"size_bytes": len(image_bytes),
			"text_content": "",
			"metadata": {}
		}
		if Image:
			try:
				image = Image.open(io.BytesIO(image_bytes))
				parsed_data["metadata"] = {
					"format": image.format,
					"size": image.size,
					"mode": image.mode
				}
				if pytesseract:
					try:
						text = pytesseract.image_to_string(image)
						parsed_data["text_content"] = text
					except Exception as e:
						logging.warning(f"OCR failed: {str(e)}")
			except Exception as e:
				logging.warning(f"Image processing failed: {str(e)}")
		return parsed_data
	except Exception as e:
		raise ImageParsingError(f"Failed to parse image: {str(e)}")
