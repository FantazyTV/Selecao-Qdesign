"""
Protein sequence and structure enricher
"""

from typing import Dict, Any, Optional
from .base_enricher import BaseEnricher
from ..logger import get_logger

logger = get_logger(__name__)


class SequenceEnricher(BaseEnricher):
    """Enrich protein sequence metadata"""
    
    # Amino acid properties (simplified)
    AA_PROPERTIES = {
        'A': {'hydrophobic': True, 'charge': 'neutral'},
        'R': {'hydrophobic': False, 'charge': 'positive'},
        'N': {'hydrophobic': False, 'charge': 'neutral'},
        'D': {'hydrophobic': False, 'charge': 'negative'},
        'C': {'hydrophobic': True, 'charge': 'neutral'},
        'Q': {'hydrophobic': False, 'charge': 'neutral'},
        'E': {'hydrophobic': False, 'charge': 'negative'},
        'G': {'hydrophobic': True, 'charge': 'neutral'},
        'H': {'hydrophobic': False, 'charge': 'positive'},
        'I': {'hydrophobic': True, 'charge': 'neutral'},
        'L': {'hydrophobic': True, 'charge': 'neutral'},
        'K': {'hydrophobic': False, 'charge': 'positive'},
        'M': {'hydrophobic': True, 'charge': 'neutral'},
        'F': {'hydrophobic': True, 'charge': 'neutral'},
        'P': {'hydrophobic': True, 'charge': 'neutral'},
        'S': {'hydrophobic': False, 'charge': 'neutral'},
        'T': {'hydrophobic': False, 'charge': 'neutral'},
        'W': {'hydrophobic': True, 'charge': 'neutral'},
        'Y': {'hydrophobic': False, 'charge': 'neutral'},
        'V': {'hydrophobic': True, 'charge': 'neutral'},
    }
    
    def enrich(
        self,
        content: str,
        metadata: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Enrich sequence metadata
        
        Args:
            content: Sequence content
            metadata: Existing metadata
            data_type: Data type
        
        Returns:
            Enhanced metadata
        """
        try:
            # Clean sequence
            sequence = content.replace(" ", "").replace("\n", "").upper()
            
            metadata["length"] = len(sequence)
            
            # Amino acid composition
            aa_counts = {}
            for aa in sequence:
                if aa != 'X':
                    aa_counts[aa] = aa_counts.get(aa, 0) + 1
            
            metadata["aa_composition"] = aa_counts
            
            # Calculate properties
            hydrophobic_count = sum(1 for aa in sequence if self.AA_PROPERTIES.get(aa, {}).get('hydrophobic', False))
            positive_count = sum(1 for aa in sequence if self.AA_PROPERTIES.get(aa, {}).get('charge') == 'positive')
            negative_count = sum(1 for aa in sequence if self.AA_PROPERTIES.get(aa, {}).get('charge') == 'negative')
            
            if len(sequence) > 0:
                metadata["hydrophobicity_ratio"] = hydrophobic_count / len(sequence)
                metadata["positive_charge_ratio"] = positive_count / len(sequence)
                metadata["negative_charge_ratio"] = negative_count / len(sequence)
                metadata["net_charge"] = positive_count - negative_count
            
            # Check for disulfide bonds (C residues)
            cysteine_count = sequence.count('C')
            metadata["cysteine_count"] = cysteine_count
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error enriching sequence: {e}")
            return metadata
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable"""
        return data_type == "sequence"


class StructureEnricher(BaseEnricher):
    """Enrich protein structure metadata"""
    
    def enrich(
        self,
        content: str,
        metadata: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Enrich structure metadata
        
        Args:
            content: Structure content (PDB format)
            metadata: Existing metadata
            data_type: Data type
        
        Returns:
            Enhanced metadata
        """
        try:
            # Count atom records
            atom_count = sum(1 for line in content.split('\n') if line.startswith('ATOM'))
            hetatm_count = sum(1 for line in content.split('\n') if line.startswith('HETATM'))
            
            metadata["atom_count"] = atom_count
            metadata["hetatm_count"] = hetatm_count
            metadata["total_atoms"] = atom_count + hetatm_count
            
            # Count secondary structure elements
            helix_count = sum(1 for line in content.split('\n') if line.startswith('HELIX'))
            sheet_count = sum(1 for line in content.split('\n') if line.startswith('SHEET'))
            
            metadata["helix_count"] = helix_count
            metadata["sheet_count"] = sheet_count
            
            # Look for crystal info
            if 'CRYST1' in content:
                metadata["is_crystal_structure"] = True
            
            # Extract header info if available
            for line in content.split('\n'):
                if line.startswith('REMARK'):
                    # Could parse REMARK lines for more info
                    pass
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error enriching structure: {e}")
            return metadata
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable"""
        return data_type == "structure"
