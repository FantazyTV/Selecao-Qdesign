"""
Text metadata enricher (lightweight version without spacy)
"""

import re
from typing import Dict, Any, Optional
from .base_enricher import BaseEnricher
from ..logger import get_logger

logger = get_logger(__name__)


class TextEnricher(BaseEnricher):
    """Enrich text metadata using lightweight text processing"""
    
    def __init__(self):
        """Initialize text enricher"""
        # Common stop words to exclude from keyword extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Common capitalized words that might be entities
        self.entity_patterns = {
            'PROTEIN': r'\b(?:protein|kinase|receptor|enzyme|antibody|antigen|hormone|peptide)\b',
            'DISEASE': r'\b(?:cancer|diabetes|disease|syndrome|disorder|infection|virus|bacterial)\b',
            'DRUG': r'\b(?:drug|compound|molecule|inhibitor|activator|agonist|antagonist)\b',
            'ORGANISM': r'\b(?:human|mouse|bacteria|virus|yeast|plant|cell)\b',
            'METHOD': r'\b(?:method|technique|assay|analysis|microscopy|sequencing|imaging)\b',
        }
    
    def _extract_key_terms(self, content: str, limit: int = 10) -> list:
        """Extract key terms from content using simple heuristics"""
        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-z]+\b', content.lower())
        
        # Filter stop words and short words
        key_terms = [
            w for w in words 
            if w not in self.stop_words and len(w) > 3
        ]
        
        # Count frequency and get top terms
        from collections import Counter
        term_freq = Counter(key_terms)
        return [term for term, _ in term_freq.most_common(limit)]
    
    def _extract_entities(self, content: str) -> Dict[str, list]:
        """Extract named entities using regex patterns"""
        entities = {}
        text_sample = content[:50000]  # Limit for performance
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text_sample, re.IGNORECASE)
            if matches:
                # Remove duplicates and limit to 5
                unique_matches = list(dict.fromkeys(matches))[:5]
                entities[entity_type] = unique_matches
        
        # Extract capitalized phrases (potential names/entities)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text_sample)
        if capitalized:
            entity_phrases = list(dict.fromkeys(capitalized))[:5]
            entities['NAMED_ENTITIES'] = entity_phrases
        
        return entities
    
    def enrich(
        self,
        content: str,
        metadata: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Enrich text metadata using lightweight processing
        
        Args:
            content: Text content
            metadata: Existing metadata
            data_type: Data type
        
        Returns:
            Enhanced metadata
        """
        try:
            # Basic statistical enrichment
            metadata["word_count"] = len(content.split())
            metadata["char_count"] = len(content)
            
            # Extract sentences (split on common sentence endings)
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            metadata["sentence_count"] = len(sentences)
            
            # Extract paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            metadata["paragraph_count"] = len(paragraphs)
            
            # Extract key terms using frequency analysis
            key_terms = self._extract_key_terms(content)
            if key_terms:
                metadata["key_terms"] = key_terms
            
            # Extract entities using regex patterns
            entities = self._extract_entities(content)
            if entities:
                metadata["entities"] = entities
            
            # Calculate average word length
            words = content.split()
            if words:
                avg_word_length = sum(len(w) for w in words) / len(words)
                metadata["avg_word_length"] = round(avg_word_length, 2)
            
            # Language detection (simple heuristic - look for English patterns)
            metadata["language"] = "en"  # Assume English for now
            
            # Content complexity (based on word count and vocabulary diversity)
            unique_words = len(set(content.lower().split()))
            total_words = metadata.get("word_count", 1)
            diversity_ratio = unique_words / total_words if total_words > 0 else 0
            metadata["vocabulary_diversity"] = round(diversity_ratio, 3)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error enriching text: {e}")
            return metadata
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable"""
        return data_type == "text"
