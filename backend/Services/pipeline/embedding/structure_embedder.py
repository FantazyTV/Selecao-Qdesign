"""Structure embedding using lightweight feature extraction"""

from typing import List, Dict, Any, Optional
import numpy as np
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class StructureEmbedder(BaseEmbedder):
    """Embed protein structures using lightweight PDB feature extraction"""

    def __init__(self):
        """Initialize structure embedder"""
        config = get_config()
        self.normalize = config.normalize_embeddings
        self.dimension = 256
        logger.info("Initialized StructureEmbedder (lightweight)")

    def _parse_pdb_minimal(self, content: str) -> Dict[str, Any]:
        """Parse PDB to extract CA coordinates"""
        ca_coords = []
        atoms = []
        residues = set()

        for line in content.split('\n'):
            if not line.startswith('ATOM'):
                continue
            try:
                atom_name = line[12:16].strip()
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                res_num = int(line[22:26])
                res_name = line[17:20].strip()

                atoms.append((atom_name, res_name, x, y, z, res_num))
                residues.add(res_num)

                if atom_name == 'CA':
                    ca_coords.append((x, y, z))
            except (ValueError, IndexError):
                pass

        return {
            'ca_coords': np.array(ca_coords, dtype=np.float32) if ca_coords else np.zeros((0, 3)),
            'atoms': atoms,
            'residues': residues
        }

    def _extract_structure_features(self, content: str) -> np.ndarray:
        """Extract 256-dim feature vector from PDB"""
        pdb_data = self._parse_pdb_minimal(content)
        ca_coords = pdb_data['ca_coords']
        features = []

        if len(ca_coords) > 0:
            # Coordinate statistics
            features.extend(ca_coords.mean(axis=0).tolist())
            features.extend(ca_coords.std(axis=0).tolist())
            features.extend(ca_coords.min(axis=0).tolist())
            features.extend(ca_coords.max(axis=0).tolist())

            # Distance statistics
            if len(ca_coords) > 1:
                distances = [np.linalg.norm(ca_coords[i+1] - ca_coords[i]) for i in range(len(ca_coords)-1)]
                distances = np.array(distances)
                features.extend([distances.mean(), distances.std(), distances.min(), distances.max()])
            else:
                features.extend([0, 0, 0, 0])

            # Radius of gyration
            centroid = ca_coords.mean(axis=0)
            rg = np.sqrt(np.mean(np.sum((ca_coords - centroid) ** 2, axis=1)))
            features.append(rg)

            # Bounding box
            bbox = ca_coords.max(axis=0) - ca_coords.min(axis=0)
            features.extend(bbox.tolist())
            features.append(np.prod(bbox))
            features.append(float(len(ca_coords)))
            features.append(float(len(pdb_data['atoms'])))
        else:
            features.extend([0] * 31)

        # Residue composition
        aa_codes = {'ALA': 0, 'GLY': 1, 'VAL': 2, 'LEU': 3, 'ILE': 4, 'PRO': 5, 'PHE': 6, 'TRP': 7, 'MET': 8, 'CYS': 9,
                    'SER': 10, 'THR': 11, 'ASN': 12, 'GLN': 13, 'ASP': 14, 'GLU': 15, 'LYS': 16, 'ARG': 17, 'HIS': 18}
        residue_names = [atom[1] for atom in pdb_data['atoms']]
        aa_counts = [residue_names.count(code) for code in aa_codes.keys()]
        total = sum(aa_counts) + 1e-8
        features.extend([c / total for c in aa_counts])

        # Secondary structure approximation
        if len(ca_coords) > 3:
            for i in range(len(ca_coords) - 3):
                v1 = ca_coords[i+1] - ca_coords[i]
                v2 = ca_coords[i+2] - ca_coords[i+1]
                cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
                features.append(np.clip(cos, -1, 1))
                if len(features) >= 200:
                    break
        features.extend([0] * (self.dimension - len(features)))

        features_array = np.array(features[:self.dimension], dtype=np.float32)
        if self.normalize:
            features_array = features_array / (np.linalg.norm(features_array) + 1e-8)

        return features_array

    def embed(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Embed single structure"""
        if not content or not content.strip():
            return np.zeros(self.dimension)
        return self._extract_structure_features(content)

    def embed_batch(self, contents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        """Embed multiple structures"""
        embeddings = [self.embed(content) for content in contents]
        return np.array(embeddings, dtype=np.float32)

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension

    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "structure"
