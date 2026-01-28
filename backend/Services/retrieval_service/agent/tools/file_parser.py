import base64
import re
import json
import io
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

try:
    import PyPDF2
    from pypdf import PdfReader
except ImportError:
    PyPDF2 = None
    PdfReader = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

try:
    from Bio import SeqIO
    from Bio.PDB import PDBParser
    from Bio.PDB.MMCIF2Dict import MMCIF2Dict
except ImportError:
    SeqIO = None
    PDBParser = None
    MMCIF2Dict = None

logger = logging.getLogger(__name__)

class FileParsingError(Exception):
    """Custom exception for file parsing errors."""
    pass

class ContentParser:
    """Handles parsing of different content types from the data pool."""
    
    @staticmethod
    def decode_content(content: str, content_type: str = "base64") -> bytes:
        """Decode content from base64 or return as bytes."""
        try:
            if content_type == "base64":
                return base64.b64decode(content)
            return content.encode('utf-8')
        except Exception as e:
            raise FileParsingError(f"Failed to decode content: {str(e)}")
    
    @staticmethod
    def parse_pdf(content: str) -> Dict[str, Any]:
        """Parse PDF content and extract text, metadata."""
        if not PyPDF2 and not PdfReader:
            raise FileParsingError("PDF parsing libraries not available")
        
        try:
            pdf_bytes = ContentParser.decode_content(content)
            pdf_file = io.BytesIO(pdf_bytes)
            
            # Try with pypdf first, fallback to PyPDF2
            try:
                if PdfReader:
                    reader = PdfReader(pdf_file)
                    pages = reader.pages
                    metadata = reader.metadata or {}
                else:
                    reader = PyPDF2.PdfReader(pdf_file)
                    pages = reader.pages
                    metadata = reader.metadata or {}
            except Exception:
                pdf_file.seek(0)
                reader = PyPDF2.PdfReader(pdf_file)
                pages = reader.pages
                metadata = reader.metadata or {}
            
            # Extract text from all pages
            text_content = ""
            page_texts = []
            for i, page in enumerate(pages):
                try:
                    page_text = page.extract_text()
                    page_texts.append({"page": i+1, "text": page_text})
                    text_content += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting text from page {i+1}: {str(e)}")
            
            # Extract key information
            parsed_data = {
                "text_content": text_content.strip(),
                "page_count": len(pages),
                "pages": page_texts,
                "metadata": {
                    "title": str(metadata.get("/Title", "")) if metadata.get("/Title") else "",
                    "author": str(metadata.get("/Author", "")) if metadata.get("/Author") else "",
                    "subject": str(metadata.get("/Subject", "")) if metadata.get("/Subject") else "",
                    "creator": str(metadata.get("/Creator", "")) if metadata.get("/Creator") else "",
                    "creation_date": str(metadata.get("/CreationDate", "")) if metadata.get("/CreationDate") else "",
                },
                "summary": ContentParser._generate_text_summary(text_content),
                "keywords": ContentParser._extract_scientific_keywords(text_content),
                "entities": ContentParser._extract_biological_entities(text_content)
            }
            
            return parsed_data
            
        except Exception as e:
            raise FileParsingError(f"Failed to parse PDF: {str(e)}")
    
    @staticmethod
    def parse_text(content: str) -> Dict[str, Any]:
        """Parse plain text content."""
        try:
            # Content might already be text or base64 encoded
            if content.strip().startswith(('JVBERi', 'data_', 'HEADER', '>')):  # Likely not plain text
                try:
                    text_content = ContentParser.decode_content(content).decode('utf-8')
                except:
                    text_content = content
            else:
                text_content = content
            
            parsed_data = {
                "text_content": text_content,
                "character_count": len(text_content),
                "word_count": len(text_content.split()),
                "line_count": len(text_content.split('\n')),
                "summary": ContentParser._generate_text_summary(text_content),
                "keywords": ContentParser._extract_scientific_keywords(text_content),
                "entities": ContentParser._extract_biological_entities(text_content),
                "code_detected": ContentParser._detect_code(text_content)
            }
            
            return parsed_data
            
        except Exception as e:
            raise FileParsingError(f"Failed to parse text: {str(e)}")
    
    @staticmethod
    def parse_cif_or_pdb(content: str, file_type: str) -> Dict[str, Any]:
        """Parse CIF or PDB structure files."""
        try:
            if file_type.lower() == 'cif':
                return ContentParser._parse_cif(content)
            else:  # PDB
                return ContentParser._parse_pdb(content)
        except Exception as e:
            raise FileParsingError(f"Failed to parse {file_type}: {str(e)}")
    
    @staticmethod
    def _parse_cif(content: str) -> Dict[str, Any]:
        """Parse mmCIF file content."""
        try:
            # Decode if base64
            if not content.strip().startswith('data_'):
                cif_content = ContentParser.decode_content(content).decode('utf-8')
            else:
                cif_content = content
            
            # Extract basic information
            lines = cif_content.split('\n')
            parsed_data = {
                "content": cif_content,
                "format": "mmCIF",
                "metadata": {},
                "entities": [],
                "structure_info": {}
            }
            
            # Extract PDB ID and basic info
            for line in lines:
                if line.startswith('data_'):
                    parsed_data["metadata"]["pdb_id"] = line.replace('data_', '').strip()
                elif '_entry.id' in line:
                    parsed_data["metadata"]["entry_id"] = line.split()[-1].strip()
                elif '_struct.title' in line:
                    title_line = line.split('_struct.title')[1].strip().strip('"\'')
                    parsed_data["metadata"]["title"] = title_line
                elif '_entity.pdbx_description' in line:
                    desc_line = line.split('_entity.pdbx_description')[1].strip().strip('"\'')
                    parsed_data["entities"].append(desc_line)
            
            # Try to use BioPython if available
            if MMCIF2Dict:
                try:
                    cif_file = io.StringIO(cif_content)
                    cif_dict = MMCIF2Dict(cif_file)
                    parsed_data["structure_info"] = {
                        "resolution": cif_dict.get("_refine.ls_d_res_high", [None])[0],
                        "space_group": cif_dict.get("_symmetry.space_group_name_H-M", [None])[0],
                        "experimental_method": cif_dict.get("_exptl.method", [None])[0]
                    }
                except Exception as e:
                    logger.warning(f"BioPython CIF parsing failed: {str(e)}")
            
            return parsed_data
            
        except Exception as e:
            raise FileParsingError(f"CIF parsing error: {str(e)}")
    
    @staticmethod
    def _parse_pdb(content: str) -> Dict[str, Any]:
        """Parse PDB file content."""
        try:
            # Decode if base64
            if not content.strip().startswith(('HEADER', 'TITLE', 'ATOM', 'REMARK')):
                pdb_content = ContentParser.decode_content(content).decode('utf-8')
            else:
                pdb_content = content
            
            lines = pdb_content.split('\n')
            parsed_data = {
                "content": pdb_content,
                "format": "PDB",
                "metadata": {},
                "entities": [],
                "structure_info": {}
            }
            
            # Extract PDB header information
            for line in lines:
                if line.startswith('HEADER'):
                    parts = line.split()
                    if len(parts) >= 4:
                        parsed_data["metadata"]["pdb_id"] = parts[-1]
                        parsed_data["metadata"]["classification"] = ' '.join(parts[1:-2])
                elif line.startswith('TITLE'):
                    title = line[10:].strip()
                    parsed_data["metadata"]["title"] = parsed_data["metadata"].get("title", "") + " " + title
                elif line.startswith('COMPND'):
                    compound = line[10:].strip()
                    parsed_data["entities"].append(compound)
                elif line.startswith('REMARK   2 RESOLUTION'):
                    resolution = line.split()[-2:-1]
                    if resolution:
                        parsed_data["structure_info"]["resolution"] = resolution[0]
            
            return parsed_data
            
        except Exception as e:
            raise FileParsingError(f"PDB parsing error: {str(e)}")
    
    @staticmethod
    def parse_image(content: str) -> Dict[str, Any]:
        """Parse image content and extract text via OCR if available."""
        try:
            image_bytes = ContentParser.decode_content(content)
            
            parsed_data = {
                "size_bytes": len(image_bytes),
                "text_content": "",
                "metadata": {}
            }
            
            if Image:
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    parsed_data["metadata"] = {
                        "format": image.format,
                        "size": image.size,
                        "mode": image.mode
                    }
                    
                    # OCR if pytesseract available
                    if pytesseract:
                        try:
                            text = pytesseract.image_to_string(image)
                            parsed_data["text_content"] = text
                            parsed_data["keywords"] = ContentParser._extract_scientific_keywords(text)
                        except Exception as e:
                            logger.warning(f"OCR failed: {str(e)}")
                            
                except Exception as e:
                    logger.warning(f"Image processing failed: {str(e)}")
            
            return parsed_data
            
        except Exception as e:
            raise FileParsingError(f"Failed to parse image: {str(e)}")
    
    @staticmethod
    def _generate_text_summary(text: str, max_length: int = 500) -> str:
        """Generate a simple extractive summary."""
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
    
    @staticmethod
    def _extract_scientific_keywords(text: str) -> List[str]:
        """Extract scientific keywords and terms."""
        if not text:
            return []
        
        # Common scientific patterns
        patterns = [
            r'\b[A-Z][a-z]+\s+[a-z]+\b',  # Species names
            r'\b\d+\.?\d*\s*[μmMnNkK]?[gGlLmM]\b',  # Measurements
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w+ase\b',  # Enzymes
            r'\b\w+ene\b|\b\w+ane\b|\b\w+yne\b',  # Chemical compounds
            r'\bprotein\b|\bgene\b|\bDNA\b|\bRNA\b|\benzyme\b',  # Biological terms
        ]
        
        keywords = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.update(match.strip() for match in matches if len(match.strip()) > 2)
        
        return list(keywords)[:50]  # Limit to 50 keywords
    
    @staticmethod
    def _extract_biological_entities(text: str) -> Dict[str, List[str]]:
        """Extract biological entities like proteins, genes, etc."""
        if not text:
            return {}
        
        entities = {
            "proteins": [],
            "genes": [],
            "chemicals": [],
            "organisms": [],
            "measurements": []
        }
        
        # Simple pattern matching for biological entities
        protein_patterns = [
            r'\b[A-Z][a-z]+\s+protein\b',
            r'\b\w+ase\b',
            r'\b[A-Z]{3,8}\b',  # Protein abbreviations
        ]
        
        for pattern in protein_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["proteins"].extend(match.strip() for match in matches)
        
        # Gene patterns
        gene_patterns = [
            r'\b[a-zA-Z]+\d+\b',  # Gene names like TP53
            r'\b[A-Z]{3,5}[0-9]+\b'
        ]
        
        for pattern in gene_patterns:
            matches = re.findall(pattern, text)
            entities["genes"].extend(match.strip() for match in matches)
        
        # Remove duplicates and limit
        for key in entities:
            entities[key] = list(set(entities[key]))[:20]
        
        return entities
    
    @staticmethod
    def _detect_code(text: str) -> bool:
        """Detect if text contains code."""
        code_indicators = [
            r'def\s+\w+\(',  # Python functions
            r'import\s+\w+',  # Import statements
            r'class\s+\w+',  # Class definitions
            r'#include\s*<',  # C/C++ includes
            r'function\s+\w+\(',  # JavaScript functions
            r'\{\s*\n.*\}\s*\n',  # Code blocks
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False

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
        logger.error(f"Failed to parse {entry_type} content: {str(e)}")
        return {
            "error": str(e),
            "original_type": entry_type,
            "name": entry_dict.get("name", ""),
            "description": entry_dict.get("description", ""),
            "_id": entry_dict.get("_id", ""),
            "parsed_at": datetime.now().isoformat()
        }