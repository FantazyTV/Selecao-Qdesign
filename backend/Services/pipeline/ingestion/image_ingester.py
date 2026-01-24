"""
Image file ingester
"""

from .base_ingester import BaseIngester, IngestedRecord
from ..logger import get_logger
from pathlib import Path

logger = get_logger(__name__)


class ImageIngester(BaseIngester):
    """Ingest image files (PNG, JPG, etc.)"""
    
    SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".tiff", ".gif", ".bmp", ".webp")
    
    def can_ingest(self, source: str) -> bool:
        """Check if source is an image file"""
        return any(source.lower().endswith(fmt) for fmt in self.SUPPORTED_FORMATS)
    
    def ingest(self, source: str, record_id: str, **kwargs) -> IngestedRecord:
        """
        Ingest image file
        
        Args:
            source: File path
            record_id: Record ID
            **kwargs: Additional arguments (extract_text=False)
        
        Returns:
            IngestedRecord
        """
        try:
            if not self.validate_file_exists(source):
                raise FileNotFoundError(f"File not found: {source}")
            
            try:
                from PIL import Image
                from PIL.Image import Exif
            except ImportError:
                raise ImportError("Pillow not installed. Install with: pip install pillow")
            
            img = Image.open(source)
            
            # Get image properties
            width, height = img.size
            format_type = img.format or "unknown"
            mode = img.mode
            
            # Get metadata from EXIF if available
            exif_data = {}
            try:
                exif = img.getexif()
                if exif:
                    for tag_id, value in exif.items():
                        try:
                            tag_name = Image.Exif.TAGS.get(tag_id, tag_id)
                            exif_data[str(tag_name)] = str(value)[:100]  # Limit value length
                        except:
                            pass
            except:
                pass
            
            # Read raw image data for potential OCR/analysis
            # Store as simple description for now
            image_description = f"Image: {width}x{height} {format_type} ({mode})"
            file_size = self.get_file_size(source)
            
            record = IngestedRecord(
                id=record_id,
                data_type="image",
                source="file",
                collection=kwargs.get("collection", "images"),
                content=image_description,
                file_path=source,
                file_size=file_size,
                content_length=file_size,  # Use file size for images
                metadata={
                    "format": format_type,
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "image_path": source,
                    "exif": exif_data if exif_data else None
                }
            )
            
            logger.info(f"Successfully ingested image: {source} ({width}x{height})")
            return record
            
        except Exception as e:
            logger.error(f"Failed to ingest image {source}: {e}")
            return IngestedRecord(
                id=record_id,
                data_type="image",
                source="file",
                collection=kwargs.get("collection", "images"),
                content="",
                file_path=source,
                error=str(e)
            )
