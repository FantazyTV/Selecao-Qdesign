"""
PDF and text file ingester
"""

from .base_ingester import BaseIngester, IngestedRecord
from ..logger import get_logger
from pathlib import Path

logger = get_logger(__name__)


class TextIngester(BaseIngester):
    """Ingest plain text files"""
    
    def can_ingest(self, source: str) -> bool:
        """Check if source is a text file"""
        return source.endswith((".txt", ".md", ".text"))
    
    def ingest(self, source: str, record_id: str, **kwargs) -> IngestedRecord:
        """
        Ingest text file
        
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
            
            file_size = self.get_file_size(source)
            
            record = IngestedRecord(
                id=record_id,
                data_type="text",
                source="file",
                collection=kwargs.get("collection", "text_files"),
                content=content,
                file_path=source,
                file_size=file_size,
                content_length=len(content),
                metadata={
                    "format": "text",
                    "encoding": "utf-8"
                }
            )
            
            logger.info(f"Successfully ingested text file: {source} ({len(content)} chars)")
            return record
            
        except Exception as e:
            logger.error(f"Failed to ingest text file {source}: {e}")
            return IngestedRecord(
                id=record_id,
                data_type="text",
                source="file",
                collection=kwargs.get("collection", "text_files"),
                content="",
                file_path=source,
                error=str(e)
            )


class PDFIngester(BaseIngester):
    """Ingest PDF files"""
    
    def can_ingest(self, source: str) -> bool:
        """Check if source is a PDF file"""
        return source.endswith(".pdf")
    
    def ingest(self, source: str, record_id: str, **kwargs) -> IngestedRecord:
        """
        Ingest PDF file
        
        Args:
            source: File path
            record_id: Record ID
            **kwargs: Additional arguments (extract_images=False)
        
        Returns:
            IngestedRecord
        """
        try:
            if not self.validate_file_exists(source):
                raise FileNotFoundError(f"File not found: {source}")
            
            try:
                import pdfplumber
            except ImportError:
                raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")
            
            content_parts = []
            
            with pdfplumber.open(source) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        content_parts.append(f"--- Page {page_num} ---\n{text}")
            
            content = "\n\n".join(content_parts)
            file_size = self.get_file_size(source)
            
            record = IngestedRecord(
                id=record_id,
                data_type="text",
                source="file",
                collection=kwargs.get("collection", "pdf_documents"),
                content=content,
                file_path=source,
                file_size=file_size,
                content_length=len(content),
                metadata={
                    "format": "pdf",
                    "num_pages": len(pdf.pages)
                }
            )
            
            logger.info(f"Successfully ingested PDF: {source} ({len(content)} chars)")
            return record
            
        except Exception as e:
            logger.error(f"Failed to ingest PDF {source}: {e}")
            return IngestedRecord(
                id=record_id,
                data_type="text",
                source="file",
                collection=kwargs.get("collection", "pdf_documents"),
                content="",
                file_path=source,
                error=str(e)
            )
