import re
from typing import List, Dict

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
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.update(match.strip() for match in matches if len(match.strip()) > 2)
    return list(keywords)

def _extract_biological_entities(text: str) -> Dict[str, List[str]]:
    if not text:
        return {}
    entities = {
        "proteins": [],
        "genes": [],
        "chemicals": [],
        "organisms": [],
        "measurements": []
    }
    protein_patterns = [
        r'\b[A-Z][a-z]+\s+protein\b',
        r'\b\w+ase\b',
        r'\b[A-Z]{3,8}\b',
    ]
    for pattern in protein_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["proteins"].extend(match.strip() for match in matches)
    gene_patterns = [
        r'\b[a-zA-Z]+\d+\b',
        r'\b[A-Z]{3,5}[0-9]+\b'
    ]
    for pattern in gene_patterns:
        matches = re.findall(pattern, text)
        entities["genes"].extend(match.strip() for match in matches)
    for key in entities:
        entities[key] = list(set(entities[key]))[:20]
    return entities

def _detect_code(text: str) -> bool:
    code_indicators = [
        r'def\s+\w+\(',
        r'import\s+\w+',
        r'class\s+\w+',
        r'#include\s*<',
        r'function\s+\w+\(',
        r'\{\s*\n.*\}\s*\n',
    ]
    for pattern in code_indicators:
        if re.search(pattern, text, re.MULTILINE):
            return True
    return False
