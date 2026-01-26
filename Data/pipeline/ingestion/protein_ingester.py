"""
Protein sequence and structure file ingester
"""

from .base_ingester import BaseIngester, IngestedRecord
from ..logger import get_logger
from pathlib import Path

logger = get_logger(__name__)


class SequenceIngester(BaseIngester):
    """Ingest protein sequence files (FASTA format)"""
    
    def can_ingest(self, source: str) -> bool:
        """Check if source is a FASTA file"""
        return source.endswith((".fasta", ".fa", ".faa", ".seq"))
    
    def ingest(self, source: str, record_id: str, **kwargs) -> IngestedRecord:
        """
        Ingest FASTA sequence file
        
        Args:
            source: File path
            record_id: Record ID
            **kwargs: Additional arguments
        
        Returns:
            IngestedRecord
        """
        try:
            if not self.validate_file_exists(source):
                raise FileNotFoundError(f"File not found: {source}")
            
            sequences = self._parse_fasta(source)
            
            # Combine all sequences for storage
            combined_content = "\n".join([f">{h}\n{s}" for h, s in sequences])
            file_size = self.get_file_size(source)
            
            record = IngestedRecord(
                id=record_id,
                data_type="sequence",
                source="file",
                collection=kwargs.get("collection", "protein_sequences"),
                content=combined_content,
                file_path=source,
                file_size=file_size,
                content_length=len(combined_content),
                metadata={
                    "format": "fasta",
                    "num_sequences": len(sequences),
                    "sequence_headers": [h for h, _ in sequences]
                }
            )
            
            logger.info(f"Successfully ingested FASTA: {source} ({len(sequences)} sequences)")
            return record
            
        except Exception as e:
            logger.error(f"Failed to ingest FASTA {source}: {e}")
            return IngestedRecord(
                id=record_id,
                data_type="sequence",
                source="file",
                collection=kwargs.get("collection", "protein_sequences"),
                content="",
                file_path=source,
                error=str(e)
            )
    
    def _parse_fasta(self, file_path: str) -> list:
        """Parse FASTA file"""
        sequences = []
        current_header = None
        current_seq = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('>'):
                    if current_header is not None:
                        sequences.append((current_header, ''.join(current_seq)))
                    current_header = line[1:]
                    current_seq = []
                else:
                    current_seq.append(line)
        
        if current_header is not None:
            sequences.append((current_header, ''.join(current_seq)))
        
        return sequences


class StructureIngester(BaseIngester):
    """Ingest protein structure files (PDB format)"""
    
    def can_ingest(self, source: str) -> bool:
        """Check if source is a PDB file"""
        return source.endswith((".pdb", ".cif", ".mmcif"))
    
    def ingest(self, source: str, record_id: str, **kwargs) -> IngestedRecord:
        """
        Ingest PDB structure file
        
        Args:
            source: File path
            record_id: Record ID
            **kwargs: Additional arguments
        
        Returns:
            IngestedRecord
        """
        try:
            if not self.validate_file_exists(source):
                raise FileNotFoundError(f"File not found: {source}")
            
            with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract basic info from PDB header
            pdb_id = Path(source).stem
            header_lines = [l for l in content.split('\n') if l.startswith('HEADER')]
            title_lines = [l for l in content.split('\n') if l.startswith('TITLE')]
            
            header_info = header_lines[0] if header_lines else ""
            title = title_lines[0] if title_lines else ""
            
            file_size = self.get_file_size(source)
            format_type = "cif" if source.endswith(".cif") or source.endswith(".mmcif") else "pdb"
            
            record = IngestedRecord(
                id=record_id,
                data_type="structure",
                source="file",
                collection=kwargs.get("collection", "protein_structures"),
                content=content,
                file_path=source,
                file_size=file_size,
                content_length=len(content),
                metadata={
                    "format": format_type,
                    "pdb_id": pdb_id,
                    "header": header_info,
                    "title": title
                }
            )
            
            logger.info(f"Successfully ingested structure: {source} ({len(content)} chars)")
            return record
            
        except Exception as e:
            logger.error(f"Failed to ingest structure {source}: {e}")
            return IngestedRecord(
                id=record_id,
                data_type="structure",
                source="file",
                collection=kwargs.get("collection", "protein_structures"),
                content="",
                file_path=source,
                error=str(e)
            )
