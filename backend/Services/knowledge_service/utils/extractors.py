"""Utility functions for text extraction and processing"""

from typing import List
import re


def extract_key_terms(text: str, min_length: int = 3) -> List[str]:
    """
    Extract key terms from project description.

    Simple keyword extraction by filtering stopwords.
    More sophisticated: use spaCy/NLP for domain-specific extraction.

    Args:
        text: Project description text
        min_length: Minimum word length to include

    Returns:
        List of key terms
    """
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "that", "this", "these", "those", "i",
        "you", "he", "she", "it", "we", "they", "what", "which", "who",
    }

    # Split and clean
    words = re.findall(r"\b\w+\b", text.lower())

    # Filter stopwords and short terms
    filtered = [
        w for w in words
        if len(w) >= min_length and w not in stopwords
    ]

    # Return unique terms in order of appearance
    seen = set()
    result = []
    for w in filtered:
        if w not in seen:
            result.append(w)
            seen.add(w)

    return result


def highlight_matches(text: str, keywords: List[str]) -> str:
    """
    Create highlighted version of text with keywords marked.

    Args:
        text: Original text
        keywords: Keywords to highlight

    Returns:
        Text with keywords wrapped in markup
    """
    result = text
    for keyword in keywords:
        pattern = rf"\b{re.escape(keyword)}\b"
        result = re.sub(pattern, f"**{keyword}**", result, flags=re.IGNORECASE)
    return result


def generate_explanation(
    similarity_score: float,
    matching_keywords: List[str],
    resource_type: str,
    source: str
) -> str:
    """
    Generate human-readable explanation for why resource is included.

    Args:
        similarity_score: Semantic similarity (0-1)
        matching_keywords: Matched keywords from description
        resource_type: Type of resource
        source: Source of resource

    Returns:
        Human-readable explanation
    """
    keyword_str = ", ".join(f"'{kw}'" for kw in matching_keywords[:3])
    score_pct = int(similarity_score * 100)

    explanation = (
        f"Matched keywords: {keyword_str}. "
        f"Semantic similarity: {score_pct}%. "
        f"Source: {source}"
    )

    return explanation
