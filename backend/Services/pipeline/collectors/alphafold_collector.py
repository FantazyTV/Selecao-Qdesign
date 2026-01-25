"""
AlphaFold Protein Structure Database collector
Fetches protein structure predictions from AlphaFold EBI API
API Documentation: https://alphafold.ebi.ac.uk/api-docs
"""

import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from .base_collector import BaseCollector, CollectorRecord
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class AlphaFoldCollector(BaseCollector):
    """Collect protein structures from AlphaFold database"""
    
    # API base URL
    API_BASE_URL = "https://alphafold.ebi.ac.uk/api"
    
    # API endpoints
    ENDPOINTS = {
        "prediction": "/prediction/{uniprot_id}",  # Get all models for a UniProt accession
        "uniprot_summary": "/uniprot/summary/{uniprot_id}.json",  # Get summary details
        "annotations": "/annotations/{uniprot_id}.json",  # Get annotations
    }
    
    def __init__(self, max_results: int = 100, batch_size: int = 10):
        """
        Initialize AlphaFold collector
        
        Args:
            max_results: Maximum number of proteins to fetch
            batch_size: Number of proteins to process in batch
        """
        super().__init__("alphafold_structures")
        self.max_results = max_results
        self.batch_size = batch_size
        config = get_config()
        self.timeout = config.collector.request_timeout
        self.max_retries = config.collector.max_retries
    
    def collect(
        self,
        uniprot_ids: List[str],
        include_annotations: bool = True,
        include_summary: bool = True
    ) -> List[CollectorRecord]:
        """
        Collect protein structures from AlphaFold
        
        Args:
            uniprot_ids: List of UniProt accession IDs
            include_annotations: Whether to fetch annotations
            include_summary: Whether to fetch UniProt summary
        
        Returns:
            List of collected records
        """
        logger.info(f"Starting AlphaFold collection for {len(uniprot_ids)} proteins")
        self.records = []
        
        # Limit to max_results
        uniprot_ids = uniprot_ids[:self.max_results]
        
        for i, uniprot_id in enumerate(uniprot_ids):
            try:
                logger.debug(f"Collecting AlphaFold data for {uniprot_id} ({i+1}/{len(uniprot_ids)})")
                
                # Get prediction data (main data)
                prediction_data = self._fetch_prediction(uniprot_id)
                
                if not prediction_data:
                    logger.warning(f"No prediction data found for {uniprot_id}")
                    continue
                
                # Get additional data
                summary_data = None
                annotations_data = None
                
                if include_summary:
                    summary_data = self._fetch_uniprot_summary(uniprot_id)
                
                if include_annotations:
                    annotations_data = self._fetch_annotations(uniprot_id)
                
                # Create record
                record = self._create_record(
                    uniprot_id,
                    prediction_data,
                    summary_data,
                    annotations_data
                )
                
                self.add_record(record)
                
            except Exception as e:
                logger.warning(f"Failed to collect AlphaFold data for {uniprot_id}: {e}")
                record = CollectorRecord(
                    data_type="structure",
                    source="alphafold",
                    collection="alphafold_structures",
                    title=f"AlphaFold structure - {uniprot_id}",
                    error=str(e),
                    metadata={"uniprot_id": uniprot_id}
                )
                self.records.append(record)
        
        logger.info(f"Successfully collected {len(self.get_valid_records())} AlphaFold structures")
        return self.records
    
    def _fetch_prediction(self, uniprot_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch prediction data for a UniProt ID
        
        Args:
            uniprot_id: UniProt accession ID
        
        Returns:
            Prediction data or None if failed
        """
        url = self.API_BASE_URL + self.ENDPOINTS["prediction"].format(uniprot_id=uniprot_id)
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to fetch prediction for {uniprot_id}: {e}")
            return None
    
    def _fetch_uniprot_summary(self, uniprot_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch UniProt summary data
        
        Args:
            uniprot_id: UniProt accession ID
        
        Returns:
            Summary data or None if failed
        """
        url = self.API_BASE_URL + self.ENDPOINTS["uniprot_summary"].format(uniprot_id=uniprot_id)
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to fetch summary for {uniprot_id}: {e}")
            return None
    
    def _fetch_annotations(self, uniprot_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch annotations for a UniProt ID
        
        Args:
            uniprot_id: UniProt accession ID
        
        Returns:
            Annotations data or None if failed
        """
        url = self.API_BASE_URL + self.ENDPOINTS["annotations"].format(uniprot_id=uniprot_id)
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to fetch annotations for {uniprot_id}: {e}")
            return None
    
    def _create_record(
        self,
        uniprot_id: str,
        prediction_data: Dict[str, Any],
        summary_data: Optional[Dict[str, Any]] = None,
        annotations_data: Optional[Dict[str, Any]] = None
    ) -> CollectorRecord:
        """
        Create a CollectorRecord from AlphaFold API data
        
        Args:
            uniprot_id: UniProt accession ID
            prediction_data: Prediction data from API
            summary_data: Optional summary data
            annotations_data: Optional annotations data
        
        Returns:
            CollectorRecord
        """
        # Extract protein name from summary
        protein_name = uniprot_id
        if summary_data and "uniprotEntry" in summary_data:
            protein_name = summary_data["uniprotEntry"].get("proteinName", uniprot_id)
        
        # Build metadata
        metadata = {
            "uniprot_id": uniprot_id,
            "source": "alphafold",
            "api_version": "1.0.0",
        }
        
        # Process prediction data
        models = []
        model_count = 0
        pld_scores = []
        pae_scores = []
        
        if isinstance(prediction_data, list):
            models = prediction_data
        elif isinstance(prediction_data, dict) and "models" in prediction_data:
            models = prediction_data.get("models", [])
        
        model_count = len(models)
        
        # Extract quality estimates from models
        for model in models:
            if "confidenceMetrics" in model:
                metrics = model["confidenceMetrics"]
                if "plddt" in metrics:
                    pld_scores.append(metrics["plddt"])
                if "pae" in metrics:
                    pae_scores.append(metrics["pae"])
        
        # Model files and URLs
        model_files = []
        for i, model in enumerate(models):
            model_info = {
                "model_id": model.get("modelId", f"model_{i}"),
                "urls": {
                    "pdb": model.get("pdbUrl", ""),
                    "mmcif": model.get("mmcifUrl", ""),
                    "bcif": model.get("bcifUrl", ""),
                }
            }
            model_files.append(model_info)
        
        metadata["models"] = {
            "count": model_count,
            "model_files": model_files,
            "plddt_scores": pld_scores,
            "pae_scores": pae_scores if pae_scores else None,
        }
        
        # Add summary information
        if summary_data:
            if "uniprotEntry" in summary_data:
                entry = summary_data["uniprotEntry"]
                metadata["uniprot"] = {
                    "accession": entry.get("accession", ""),
                    "id": entry.get("id", ""),
                    "protein_name": entry.get("proteinName", ""),
                    "organism": entry.get("organism", {}),
                    "sequence_length": entry.get("sequenceLength", 0),
                    "gene_names": entry.get("geneNames", []),
                    "function": entry.get("function", ""),
                    "cellular_location": entry.get("cellularLocation", ""),
                    "tissue_specificity": entry.get("tissueSpecificity", ""),
                }
            
            if "structures" in summary_data:
                metadata["experimental_structures"] = summary_data["structures"]
        
        # Add annotations
        if annotations_data:
            metadata["annotations"] = {
                "count": len(annotations_data) if isinstance(annotations_data, list) else 0,
                "data": annotations_data
            }
        
        # Build raw content (human-readable summary)
        raw_content = self._build_content_summary(
            uniprot_id,
            protein_name,
            metadata
        )
        
        record = CollectorRecord(
            data_type="structure",
            source="alphafold",
            collection="alphafold_structures",
            title=f"AlphaFold structure - {protein_name} ({uniprot_id})",
            description=f"AlphaFold predicted structures for {protein_name}",
            raw_content=raw_content,
            source_url=f"https://alphafold.ebi.ac.uk/entry/{uniprot_id}",
            metadata=metadata,
            date_published=datetime.utcnow()
        )
        
        return record
    
    def _build_content_summary(
        self,
        uniprot_id: str,
        protein_name: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Build a human-readable content summary
        
        Args:
            uniprot_id: UniProt ID
            protein_name: Protein name
            metadata: Metadata dictionary
        
        Returns:
            Content summary as string
        """
        content = []
        content.append(f"# AlphaFold Structure Prediction")
        content.append(f"\n## Protein Information")
        content.append(f"- **UniProt ID**: {uniprot_id}")
        content.append(f"- **Protein Name**: {protein_name}")
        
        if "uniprot" in metadata:
            up = metadata["uniprot"]
            content.append(f"- **Sequence Length**: {up.get('sequence_length', 'N/A')} amino acids")
            
            if up.get("organism"):
                organism = up["organism"]
                content.append(f"- **Organism**: {organism.get('scientificName', organism.get('commonName', 'N/A'))}")
            
            if up.get("function"):
                content.append(f"- **Function**: {up['function']}")
            
            if up.get("cellular_location"):
                content.append(f"- **Cellular Location**: {up['cellular_location']}")
        
        content.append(f"\n## Structure Models")
        if "models" in metadata:
            models_info = metadata["models"]
            content.append(f"- **Number of Models**: {models_info.get('count', 0)}")
            
            if models_info.get("plddt_scores"):
                avg_plddt = sum(models_info["plddt_scores"]) / len(models_info["plddt_scores"])
                content.append(f"- **Average pLDDT Score**: {avg_plddt:.2f}")
                content.append(f"- **pLDDT Scores**: {models_info['plddt_scores']}")
            
            if models_info.get("model_files"):
                content.append(f"\n### Model Files")
                for model in models_info["model_files"]:
                    content.append(f"  - **{model.get('model_id')}**:")
                    urls = model.get("urls", {})
                    for fmt, url in urls.items():
                        if url:
                            content.append(f"    - {fmt.upper()}: {url}")
        
        if "experimental_structures" in metadata:
            exp_structs = metadata["experimental_structures"]
            if exp_structs:
                content.append(f"\n## Experimental Structures")
                content.append(f"- **Count**: {len(exp_structs)}")
        
        content.append(f"\n## Source")
        content.append(f"- **Database**: AlphaFold Protein Structure Database")
        content.append(f"- **Entry URL**: https://alphafold.ebi.ac.uk/entry/{uniprot_id}")
        
        return "\n".join(content)
    
    def validate(self, record: CollectorRecord) -> bool:
        """
        Validate an AlphaFold record
        
        Args:
            record: Record to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not record.metadata:
            return False
        
        if "uniprot_id" not in record.metadata:
            return False
        
        if "models" not in record.metadata:
            return False
        
        # Ensure models has count
        models_info = record.metadata.get("models", {})
        if models_info.get("count", 0) == 0:
            return False
        
        return True
