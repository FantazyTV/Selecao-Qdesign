"""
Protein sequence and structure normalizer
"""

import re
from typing import Dict, Any, Optional
from .normalizer import BaseNormalizer
from ..logger import get_logger

logger = get_logger(__name__)


class SequenceNormalizer(BaseNormalizer):
    """Normalize protein sequences"""
    
    # Standard amino acids
    VALID_AA = set('ACDEFGHIKLMNPQRSTVWY')
    
    def normalize(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Normalize sequence content
        
        Args:
            content: Sequence to normalize
            metadata: Optional metadata
        
        Returns:
            Normalized sequence
        """
        try:
            # Remove whitespace
            content = re.sub(r'\s+', '', content)
            
            # Convert to uppercase
            content = content.upper()
            
            # Remove numbers and special characters (keep only amino acids)
            content = ''.join(c for c in content if c in self.VALID_AA or c == 'X')
            
            # Remove empty sequences
            if not content:
                logger.warning("Empty sequence after normalization")
            
            return content
            
        except Exception as e:
            logger.error(f"Error normalizing sequence: {e}")
            return content
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "sequence"


class StructureNormalizer(BaseNormalizer):
    """Normalize protein structure files"""
    
    def normalize(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Normalize structure content
        
        Args:
            content: Structure content (PDB/CIF format)
            metadata: Optional metadata
        
        Returns:
            Normalized structure
        """
        try:
            # For now, just clean up whitespace and normalize line endings
            lines = content.split('\n')
            
            # Keep meaningful lines (ATOM, HETATM, CONECT, etc.)
            # Skip REMARK, TITLE lines unless they're important
            cleaned_lines = []
            for line in lines:
                # Keep structural data
                if any(line.startswith(prefix) for prefix in ['ATOM', 'HETATM', 'CONECT', 'SHEET', 'HELIX']):
                    cleaned_lines.append(line.rstrip())
                # Keep header info
                elif any(line.startswith(prefix) for prefix in ['HEADER', 'TITLE', 'COMPOUND']):
                    cleaned_lines.append(line.rstrip())
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            logger.error(f"Error normalizing structure: {e}")
            return content
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "structure"
