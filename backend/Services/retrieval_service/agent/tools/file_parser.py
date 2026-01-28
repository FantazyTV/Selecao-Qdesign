import base64
from typing import Dict, Any
from agent.tools.parser.pdf_parser import parse_pdf
from agent.tools.parser.image_parser import parse_image
from agent.tools.parser.text_parser import parse_text
from agent.tools.parser.cif_parser import parse_cif_file

from datetime import datetime

class FileParsingError(Exception):
    pass


class ContentParser:
    @staticmethod
    def decode_content(content: str, content_type: str = "base64") -> bytes:
        try:
            if content_type == "base64":
                return base64.b64decode(content)
            return content.encode('utf-8')
        except Exception as e:
            raise FileParsingError(f"Failed to decode content: {str(e)}")

    @staticmethod
    def parse_pdf(content: str) -> Dict[str, Any]:
        return parse_pdf(content, ContentParser.decode_content)

    @staticmethod
    def parse_image(content: str) -> Dict[str, Any]:
        return parse_image(content, ContentParser.decode_content)

    @staticmethod
    def parse_text(content: str) -> Dict[str, Any]:
        return parse_text(content)

    @staticmethod
    def parse_cif(content: str) -> Dict[str, Any]:
        return parse_cif_file(content)

def parse_data_entry(entry_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single data entry based on its type."""
    entry_type = entry_dict.get("type", "unknown").lower()
    content = entry_dict.get("content", "")
    try:
        if entry_type == "pdf":
            parsed = ContentParser.parse_pdf(content)
        elif entry_type == "text":
            parsed = ContentParser.parse_text(content)
        elif entry_type == "image":
            parsed = ContentParser.parse_image(content)
        elif entry_type == "cif":
            parsed = ContentParser.parse_cif(content)
        else:
            parsed = ContentParser.parse_text(content)
        parsed["original_type"] = entry_type
        parsed["name"] = entry_dict.get("name", "")
        parsed["description"] = entry_dict.get("description", "")
        parsed["_id"] = entry_dict.get("_id", "")
        from datetime import datetime
        parsed["parsed_at"] = datetime.now().isoformat()
        return parsed
    except Exception as e:
        import logging
        logging.error(f"Failed to parse {entry_type} content: {str(e)}")
        from datetime import datetime
        return {
            "error": str(e),
            "original_type": entry_type,
            "name": entry_dict.get("name", ""),
            "description": entry_dict.get("description", ""),
            "_id": entry_dict.get("_id", ""),
            "parsed_at": datetime.now().isoformat()
        }

def parse_data_entry(entry_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single data entry based on its type."""
    entry_type = entry_dict.get("type", "unknown").lower()
    content = entry_dict.get("content", "")
    
    try:
        if entry_type == "pdf":
            parsed = ContentParser.parse_pdf(content)
        elif entry_type == "text":
            parsed = ContentParser.parse_text(content)
        elif entry_type in ["cif", "pdb"]:
            parsed = ContentParser.parse_cif_or_pdb(content, entry_type)
        elif entry_type == "image":
            parsed = ContentParser.parse_image(content)
        else:
            # Default text parsing for unknown types
            parsed = ContentParser.parse_text(content)
        
        # Add common metadata
        parsed["original_type"] = entry_type
        parsed["name"] = entry_dict.get("name", "")
        parsed["description"] = entry_dict.get("description", "")
        parsed["_id"] = entry_dict.get("_id", "")
        parsed["parsed_at"] = datetime.now().isoformat()
        
        return parsed
        
    except Exception as e:
        print(f"Failed to parse {entry_type} content: {str(e)}")
        return {
            "error": str(e),
            "original_type": entry_type,
            "name": entry_dict.get("name", ""),
            "description": entry_dict.get("description", ""),
            "_id": entry_dict.get("_id", ""),
            "parsed_at": datetime.now().isoformat()
        }