from typing import Dict, Any
import re

class TextParsingError(Exception):
	pass

def parse_text(content: str) -> Dict[str, Any]:
	try:
		text_content = content
		parsed_data = {
			"text_content": text_content,
			"character_count": len(text_content),
			"word_count": len(text_content.split()),
			"line_count": len(text_content.split('\n')),
			"summary": _generate_text_summary(text_content),
			"keywords": _extract_scientific_keywords(text_content),
		}
		return parsed_data
	except Exception as e:
		raise TextParsingError(f"Failed to parse text: {str(e)}")

def _generate_text_summary(text: str, max_length: int = 500) -> str:
	if not text or len(text) < max_length:
		return text
	sentences = re.split(r'[.!?]+', text)
	summary_sentences = []
	current_length = 0
	for sentence in sentences:
		sentence = sentence.strip()
		if current_length + len(sentence) < max_length:
			summary_sentences.append(sentence)
			current_length += len(sentence)
		else:
			break
	return '. '.join(summary_sentences) + ('.' if summary_sentences else '')

def _extract_scientific_keywords(text: str):
	if not text:
		return []
	patterns = [
		r'\b[A-Z][a-z]+\s+[a-z]+\b',
		r'\b\d+\.?\d*\s*[μmMnNkK]?[gGlLmM]\b',
		r'\b[A-Z]{2,}\b',
		r'\b\w+ase\b',
		r'\b\w+ene\b|\b\w+ane\b|\b\w+yne\b',
		r'\bprotein\b|\bgene\b|\bDNA\b|\bRNA\b|\benzyme\b',
	]
	keywords = set()
	for pattern in patterns:
		import re
		matches = re.findall(pattern, text, re.IGNORECASE)
		keywords.update(match.strip() for match in matches if len(match.strip()) > 2)
	return list(keywords)
