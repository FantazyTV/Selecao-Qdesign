"""
Text, image, and sequence embedder using fastembed
No torch required - lightweight and fast!
"""

from typing import List, Dict, Any, Optional
import numpy as np
from ..embedding.base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class FastembedTextEmbedder(BaseEmbedder):
    """Embed text using fastembed"""
    
    def __init__(self):
        """Initialize fastembed for text embedding"""
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        
        try:
            # Try using sentence-transformers directly (faster, no ONNX issues)
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
            self.dimension = 384  # all-MiniLM-L6-v2 dimension
            logger.info(f"Initialized FastEmbedTextEmbedder with SentenceTransformer")
        except ImportError:
            try:
                # Fallback to fastembed if sentence-transformers not available
                from fastembed import TextEmbedding
                self.model = TextEmbedding(model_name=config.fastembed_model, device=self.device)
                self.dimension = 384  # Default dimension for standard fastembed models
                logger.info(f"Initialized FastEmbedTextEmbedder with fastembed model {config.fastembed_model}")
            except ImportError:
                raise ImportError("Neither sentence-transformers nor fastembed installed. Install with: pip install sentence-transformers")
    
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Embed a single text
        
        Args:
            content: Text to embed
            metadata: Optional metadata
        
        Returns:
            Embedding vector
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for embedding")
            return np.zeros(self.dimension)
        
        try:
            # Check if using SentenceTransformer or fastembed
            if hasattr(self.model, 'encode'):
                # SentenceTransformer
                embedding = self.model.encode(content, convert_to_numpy=True)
            else:
                # fastembed
                embeddings = list(self.model.embed([content]))
                embedding = embeddings[0]
            
            if self.normalize:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Embed multiple texts
        
        Args:
            contents: List of texts to embed
            metadata: Optional list of metadata dicts
        
        Returns:
            Batch of embeddings (num_items, embedding_dim)
        """
        try:
            # Filter empty contents
            valid_contents = [c for c in contents if c and c.strip()]
            
            if not valid_contents:
                logger.warning("No valid content provided for batch embedding")
                return np.zeros((len(contents), self.dimension))
            
            # Check if using SentenceTransformer or fastembed
            if hasattr(self.model, 'encode'):
                # SentenceTransformer
                embeddings = self.model.encode(valid_contents, convert_to_numpy=True, batch_size=self.batch_size)
            else:
                # fastembed
                embeddings = list(self.model.embed(valid_contents, batch_size=self.batch_size))
            
            if self.normalize:
                embeddings = [e / (np.linalg.norm(e) + 1e-8) for e in embeddings]
            
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return np.zeros((len(contents), self.dimension))
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "text"


class FastembedSequenceEmbedder(BaseEmbedder):
    """Embed protein sequences using fastembed (no torch!)
    
    Lightweight alternative to ESM. No heavy dependencies.
    Works by treating sequences as special text.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize fastembed for sequence embedding"""
        config = get_config()
        self.device = config.device
        self.model_name = model_name
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        
        try:
            from fastembed import TextEmbedding
            self.model = TextEmbedding(model_name=self.model_name, device=self.device)
            self.dimension = 384  # Default dimension
            logger.info(f"Initialized FastembedSequenceEmbedder (lightweight, no torch!) with {model_name}")
        except ImportError:
            raise ImportError("fastembed not installed. Install with: pip install fastembed")
    
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """Embed a single sequence"""
        if not content or not content.strip():
            logger.warning("Empty sequence provided for embedding")
            return np.zeros(self.dimension)
        
        try:
            # Clean sequence
            content = content.replace(" ", "").replace("\n", "").upper()
            
            embeddings = list(self.model.embed([content]))
            embedding = embeddings[0]
            
            if self.normalize:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding sequence: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """Embed multiple sequences"""
        try:
            # Clean sequences
            valid_contents = [c.replace(" ", "").replace("\n", "").upper() for c in contents if c]
            
            if not valid_contents:
                logger.warning("No valid sequences provided for batch embedding")
                return np.zeros((len(contents), self.dimension))
            
            embeddings = list(self.model.embed(valid_contents, batch_size=self.batch_size))
            
            if self.normalize:
                embeddings = [e / (np.linalg.norm(e) + 1e-8) for e in embeddings]
            
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return np.zeros((len(contents), self.dimension))
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "sequence"


class FastembedImageEmbedder(BaseEmbedder):
    """Embed images using lightweight methods (CLIP via fastembed, fallback to PIL features)"""
    
    def __init__(self):
        """Initialize image embedder with fallback chain"""
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        self.model = None
        self.use_fastembed = False
        self.dimension = 512  # Default for CLIP
        
        # Try fastembed first
        try:
            from fastembed import ImageEmbedding
            self.model = ImageEmbedding(model_name="Qdrant/clip-ViT-B-32-vision", device=self.device)
            self.use_fastembed = True
            self.dimension = 512
            logger.info(" FastembedImageEmbedder using fastembed (CLIP ViT-B-32)")
        except Exception as e:
            logger.warning(f"fastembed CLIP not available: {e}")
            # Try PIL fallback
            try:
                from PIL import Image
                self.pil_available = True
                self.dimension = 3072  # PIL histogram features
                logger.info(" FastembedImageEmbedder using PIL fallback (3072-dim features)")
            except ImportError:
                logger.warning("PIL not available, using zero embeddings")
                self.pil_available = False
                self.dimension = 3072
    
    def _extract_pil_features(self, image_path: str) -> np.ndarray:
        """Extract lightweight features from image using PIL"""
        try:
            from PIL import Image
            import os
            
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                return np.zeros(self.dimension)
            
            img = Image.open(image_path).convert('RGB')
            
            # Extract multiple types of features
            features = []
            
            # 1. Histogram features (256 * 3 = 768 dims)
            for channel in img.split():
                hist = np.array(channel.histogram(), dtype=np.float32)
                hist = hist / (hist.sum() + 1e-8)  # Normalize
                features.append(hist)
            
            # 2. Image properties (32 dims)
            img_array = np.array(img, dtype=np.float32)
            props = []
            
            # Basic statistics
            props.append(img_array.mean())
            props.append(img_array.std())
            props.append(img_array.min())
            props.append(img_array.max())
            
            # Channel statistics
            for channel in img.split():
                ch_array = np.array(channel, dtype=np.float32)
                props.extend([ch_array.mean(), ch_array.std()])
            
            # Spatial properties
            props.append(float(img.width))
            props.append(float(img.height))
            props.append(float(img.width) / (img.height + 1e-8))  # Aspect ratio
            props.append(float(img.width * img.height))  # Total pixels
            
            # Edge detection (128 dims)
            try:
                import scipy.ndimage
                edges = scipy.ndimage.sobel(np.array(img.convert('L'), dtype=np.float32))
                edge_features = []
                for i in range(0, 128):
                    edge_features.append(edges.flatten()[min(i * len(edges.flatten()) // 128, len(edges.flatten())-1)])
                features.append(np.array(edge_features))
            except:
                features.append(np.zeros(128))
            
            # Combine all features
            all_features = np.concatenate([np.concatenate(features[:3]), np.array(props), features[-1]])
            
            # Pad or trim to exact dimension
            if len(all_features) < self.dimension:
                all_features = np.pad(all_features, (0, self.dimension - len(all_features)))
            else:
                all_features = all_features[:self.dimension]
            
            if self.normalize:
                all_features = all_features / (np.linalg.norm(all_features) + 1e-8)
            
            return np.array(all_features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error extracting PIL features: {e}")
            return np.zeros(self.dimension)
    
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Embed a single image
        
        Args:
            content: Image file path or image content descriptor
            metadata: Optional metadata (must include 'image_path')
        
        Returns:
            Embedding vector
        """
        try:
            image_path = metadata.get("image_path") if metadata else content
            
            if not image_path:
                logger.warning("No image path provided for embedding")
                return np.zeros(self.dimension)
            
            if self.use_fastembed and self.model:
                try:
                    embeddings = list(self.model.embed([image_path]))
                    embedding = embeddings[0]
                except Exception as e:
                    logger.warning(f"fastembed failed, falling back to PIL: {e}")
                    embedding = self._extract_pil_features(image_path)
            else:
                embedding = self._extract_pil_features(image_path)
            
            if self.normalize and not self.use_fastembed:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding image: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Embed multiple images
        
        Args:
            contents: List of image paths or descriptors
            metadata: Optional list of metadata dicts
        
        Returns:
            Batch of embeddings
        """
        try:
            # Extract image paths from metadata if provided
            if metadata:
                image_paths = [m.get("image_path", c) for m, c in zip(metadata, contents)]
            else:
                image_paths = contents
            
            # Filter valid paths
            valid_paths = [p for p in image_paths if p]
            
            if not valid_paths:
                logger.warning("No valid image paths provided for batch embedding")
                return np.zeros((len(contents), self.dimension))
            
            embeddings = []
            for path in valid_paths:
                embeddings.append(self.embed(path, {"image_path": path}))
            
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding image batch: {e}")
            return np.zeros((len(contents), self.dimension))
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "image"


class StructureEmbedder(BaseEmbedder):
    """Embed protein structures using lightweight feature extraction
    
    Extracts structural properties from PDB files without heavy dependencies:
    - Atomic coordinate statistics (C-alpha atoms)
    - Secondary structure distribution (alpha/beta content)
    - Residue composition and properties
    - Structural parameters (radius of gyration, etc)
    """
    
    def __init__(self):
        """Initialize structure embedder"""
        config = get_config()
        self.normalize = config.normalize_embeddings
        self.dimension = 256  # Fixed dimension for structure features
        logger.info(" StructureEmbedder initialized (lightweight, no dependencies)")
    
    def _parse_pdb_minimal(self, content: str) -> Dict[str, Any]:
        """Minimal PDB parsing to extract CA coordinates and info"""
        try:
            ca_coords = []
            atoms = []
            residues = set()
            
            for line in content.split('\n'):
                if line.startswith('ATOM'):
                    try:
                        atom_name = line[12:16].strip()
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                        res_num = int(line[22:26])
                        res_name = line[17:20].strip()
                        
                        atoms.append((atom_name, res_name, x, y, z, res_num))
                        residues.add(res_num)
                        
                        if atom_name == 'CA':  # Alpha carbon
                            ca_coords.append((x, y, z))
                    except (ValueError, IndexError):
                        pass
            
            return {
                'ca_coords': np.array(ca_coords, dtype=np.float32) if ca_coords else np.zeros((0, 3)),
                'atoms': atoms,
                'residues': residues,
                'num_atoms': len(atoms),
                'num_residues': len(residues)
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDB: {e}")
            return {'ca_coords': np.zeros((0, 3)), 'atoms': [], 'residues': set(), 'num_atoms': 0, 'num_residues': 0}
    
    def _extract_structure_features(self, content: str) -> np.ndarray:
        """Extract 256-dim feature vector from PDB structure"""
        try:
            pdb_data = self._parse_pdb_minimal(content)
            ca_coords = pdb_data['ca_coords']
            features = []
            
            # 1. Coordinate statistics (32 dims)
            if len(ca_coords) > 0:
                # Position statistics
                features.extend(ca_coords.mean(axis=0).tolist())  # 3
                features.extend(ca_coords.std(axis=0).tolist())   # 3
                features.extend(ca_coords.min(axis=0).tolist())   # 3
                features.extend(ca_coords.max(axis=0).tolist())   # 3
                
                # Distance statistics
                if len(ca_coords) > 1:
                    distances = []
                    for i in range(len(ca_coords)-1):
                        dist = np.linalg.norm(ca_coords[i+1] - ca_coords[i])
                        distances.append(dist)
                    distances = np.array(distances)
                    features.extend([distances.mean(), distances.std(), distances.min(), distances.max()])  # 4
                    
                    # Angle statistics (pseudo-dihedral angles)
                    angles = []
                    for i in range(1, len(ca_coords)-1):
                        v1 = ca_coords[i] - ca_coords[i-1]
                        v2 = ca_coords[i+1] - ca_coords[i]
                        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
                        angles.append(np.arccos(np.clip(cos_angle, -1, 1)))
                    if angles:
                        angles = np.array(angles)
                        features.extend([angles.mean(), angles.std(), angles.min(), angles.max()])  # 4
                else:
                    features.extend([0, 0, 0, 0, 0, 0, 0, 0])
                
                # Radius of gyration
                centroid = ca_coords.mean(axis=0)
                rg = np.sqrt(np.mean(np.sum((ca_coords - centroid) ** 2, axis=1)))
                features.append(rg)  # 1
                
                # Bounding box
                bbox = ca_coords.max(axis=0) - ca_coords.min(axis=0)
                features.extend(bbox.tolist())  # 3
                features.append(np.prod(bbox))  # Volume
                
                # Dimensions
                features.append(float(len(ca_coords)))  # Number of residues
                features.append(float(len(pdb_data['atoms'])))  # Number of atoms
            else:
                features.extend([0] * 31)
            
            # 2. Residue composition (32 dims - one-hot encoding for most common residues)
            residue_names = [atom[1] for atom in pdb_data['atoms']]
            aa_codes = {
                'ALA': 0, 'GLY': 1, 'VAL': 2, 'LEU': 3, 'ILE': 4,
                'PRO': 5, 'PHE': 6, 'TRP': 7, 'MET': 8, 'CYS': 9,
                'SER': 10, 'THR': 11, 'ASN': 12, 'GLN': 13, 'ASP': 14,
                'GLU': 15, 'LYS': 16, 'ARG': 17, 'HIS': 18,
                'HOH': 19, 'HEM': 20, 'LIG': 21
            }
            aa_counts = [0] * 22
            for res in residue_names:
                if res in aa_codes:
                    aa_counts[aa_codes[res]] += 1
            total = sum(aa_counts) + 1e-8
            features.extend([c / total for c in aa_counts])  # 22 normalized counts
            
            # 3. Secondary structure prediction (32 dims)
            # Simple heuristics based on CA distances and angles
            if len(ca_coords) > 3:
                sec_struct = []
                for i in range(len(ca_coords) - 3):
                    v1 = ca_coords[i+1] - ca_coords[i]
                    v2 = ca_coords[i+2] - ca_coords[i+1]
                    v3 = ca_coords[i+3] - ca_coords[i+2]
                    
                    # Angle indicators (alpha: small angles, beta: varying)
                    cos_12 = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
                    cos_23 = np.dot(v2, v3) / (np.linalg.norm(v2) * np.linalg.norm(v3) + 1e-8)
                    
                    sec_struct.append([np.clip(cos_12, -1, 1), np.clip(cos_23, -1, 1)])
                
                if sec_struct:
                    sec_struct = np.array(sec_struct)
                    features.extend(sec_struct.flatten()[:32].tolist())
                else:
                    features.extend([0] * 32)
            else:
                features.extend([0] * 32)
            
            # 4. Structural complexity metrics (64 dims)
            if len(ca_coords) > 0:
                # Fractal dimension approximation
                for scale in range(8):
                    if len(ca_coords) > 2 ** (scale + 1):
                        points_at_scale = ca_coords[::2**(scale+1)]
                        if len(points_at_scale) > 1:
                            dists = []
                            for i in range(min(10, len(points_at_scale)-1)):
                                d = np.linalg.norm(points_at_scale[i+1] - points_at_scale[i])
                                dists.append(d)
                            features.append(np.mean(dists) if dists else 0)
                        else:
                            features.append(0)
                    else:
                        features.append(0)
                
                # Local densities (window sizes of 5, 10, 15, 20)
                for window in [5, 10, 15, 20]:
                    densities = []
                    for i in range(0, len(ca_coords) - window, window):
                        window_coords = ca_coords[i:i+window]
                        centroid = window_coords.mean(axis=0)
                        density = window / (np.mean(np.linalg.norm(window_coords - centroid, axis=1)) + 1e-8)
                        densities.append(density)
                    if densities:
                        features.extend([np.mean(densities), np.std(densities)])
                    else:
                        features.extend([0, 0])
                
                # Contacts (atoms within 5 angstroms)
                contacts = 0
                if len(pdb_data['atoms']) > 0:
                    atoms_array = np.array([(a[2], a[3], a[4]) for a in pdb_data['atoms']], dtype=np.float32)
                    # Sample contacts (don't compute all for large structures)
                    sample_size = min(100, len(atoms_array))
                    for i in range(sample_size):
                        for j in range(i+1, min(i+10, len(atoms_array))):
                            dist = np.linalg.norm(atoms_array[i] - atoms_array[j])
                            if dist < 5.0:
                                contacts += 1
                features.append(float(contacts))
                
                # Hydrophobic effect (simple residue-based)
                hydrophobic_residues = {'ALA', 'VAL', 'LEU', 'ILE', 'MET', 'PHE', 'TRP', 'PRO'}
                hydro_count = sum(1 for r in residue_names if r in hydrophobic_residues)
                features.append(float(hydro_count) / (len(residue_names) + 1e-8))
                
                # Charge distribution
                charged_residues = {'LYS': 1, 'ARG': 1, 'ASP': -1, 'GLU': -1, 'HIS': 0.1}
                net_charge = sum(charged_residues.get(r, 0) for r in residue_names)
                features.append(float(net_charge))
            else:
                features.extend([0] * 64)
            
            # Ensure exactly 256 dimensions
            features_array = np.array(features, dtype=np.float32)
            if len(features_array) < self.dimension:
                features_array = np.pad(features_array, (0, self.dimension - len(features_array)))
            else:
                features_array = features_array[:self.dimension]
            
            if self.normalize:
                features_array = features_array / (np.linalg.norm(features_array) + 1e-8)
            
            return features_array
            
        except Exception as e:
            logger.error(f"Error extracting structure features: {e}")
            return np.zeros(self.dimension)
    
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Embed a single protein structure
        
        Args:
            content: PDB file content as string
            metadata: Optional metadata
        
        Returns:
            Embedding vector (256-dim)
        """
        if not content or not content.strip():
            logger.warning("Empty structure content provided for embedding")
            return np.zeros(self.dimension)
        
        return self._extract_structure_features(content)
    
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Embed multiple protein structures
        
        Args:
            contents: List of PDB file contents
            metadata: Optional metadata list
        
        Returns:
            Batch of embeddings (num_items, 256)
        """
        embeddings = []
        for content in contents:
            embeddings.append(self.embed(content))
        
        return np.array(embeddings, dtype=np.float32)
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "structure"
