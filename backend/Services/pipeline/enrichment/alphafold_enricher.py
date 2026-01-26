"""
AlphaFold structure data enricher
Enriches AlphaFold structure metadata with quality analysis and visualization support
"""

from typing import Dict, Any
from .base_enricher import BaseEnricher
from ..logger import get_logger

logger = get_logger(__name__)


class AlphaFoldEnricher(BaseEnricher):
    """Enrich AlphaFold structure metadata with quality metrics and analysis"""
    
    # pLDDT confidence score interpretation
    PLDDT_INTERPRETATION = {
        "very_high": (90, 100, "Very high confidence"),
        "high": (70, 90, "High confidence"),
        "medium": (50, 70, "Medium confidence"),
        "low": (0, 50, "Low confidence"),
    }
    
    # pAE (Predicted Aligned Error) interpretation
    PAE_INTERPRETATION = {
        "very_good": (0, 5, "Very good"),
        "good": (5, 10, "Good"),
        "moderate": (10, 20, "Moderate"),
        "poor": (20, float('inf'), "Poor"),
    }
    
    def enrich(
        self,
        content: str,
        metadata: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """
        Enrich AlphaFold structure metadata
        
        Args:
            content: Content/summary text
            metadata: Existing metadata
            data_type: Data type (should be "structure")
        
        Returns:
            Enhanced metadata
        """
        try:
            if "models" not in metadata:
                return metadata
            
            models_info = metadata["models"]
            
            # Analyze pLDDT scores
            plddt_scores = models_info.get("plddt_scores", [])
            if plddt_scores:
                self._enrich_plddt_scores(metadata, plddt_scores)
            
            # Analyze pAE scores
            pae_scores = models_info.get("pae_scores", [])
            if pae_scores:
                self._enrich_pae_scores(metadata, pae_scores)
            
            # Add model analysis
            self._enrich_model_analysis(metadata, models_info)
            
            # Add UniProt information
            if "uniprot" in metadata:
                self._enrich_uniprot_info(metadata)
            
            # Add quality classification
            self._classify_structure_quality(metadata)
            
            # Add recommended use cases
            self._add_use_case_recommendations(metadata)
            
            logger.debug(f"Successfully enriched AlphaFold metadata for {metadata.get('uniprot_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error enriching AlphaFold metadata: {e}")
        
        return metadata
    
    def _enrich_plddt_scores(self, metadata: Dict[str, Any], plddt_scores: list) -> None:
        """
        Analyze and enrich pLDDT score information
        
        Args:
            metadata: Metadata dictionary to enrich
            plddt_scores: List of pLDDT scores
        """
        if not plddt_scores:
            return
        
        avg_plddt = sum(plddt_scores) / len(plddt_scores)
        min_plddt = min(plddt_scores)
        max_plddt = max(plddt_scores)
        
        # Classify scores
        plddt_classifications = []
        for score in plddt_scores:
            for key, (min_val, max_val, label) in self.PLDDT_INTERPRETATION.items():
                if min_val <= score <= max_val:
                    plddt_classifications.append({
                        "score": score,
                        "classification": key,
                        "label": label
                    })
                    break
        
        # Add to metadata
        if "models" not in metadata:
            metadata["models"] = {}
        
        metadata["models"]["plddt_analysis"] = {
            "average": round(avg_plddt, 2),
            "minimum": round(min_plddt, 2),
            "maximum": round(max_plddt, 2),
            "scores": plddt_scores,
            "classifications": plddt_classifications,
            "overall_confidence": self._get_confidence_level(avg_plddt)
        }
    
    def _enrich_pae_scores(self, metadata: Dict[str, Any], pae_scores: list) -> None:
        """
        Analyze and enrich pAE score information
        
        Args:
            metadata: Metadata dictionary to enrich
            pae_scores: List of pAE scores
        """
        if not pae_scores:
            return
        
        avg_pae = sum(pae_scores) / len(pae_scores)
        min_pae = min(pae_scores)
        max_pae = max(pae_scores)
        
        # Classify scores
        pae_classifications = []
        for score in pae_scores:
            for key, (min_val, max_val, label) in self.PAE_INTERPRETATION.items():
                if min_val <= score <= max_val:
                    pae_classifications.append({
                        "score": round(score, 2),
                        "classification": key,
                        "label": label
                    })
                    break
        
        # Add to metadata
        if "models" not in metadata:
            metadata["models"] = {}
        
        metadata["models"]["pae_analysis"] = {
            "average": round(avg_pae, 2),
            "minimum": round(min_pae, 2),
            "maximum": round(max_pae, 2),
            "scores": pae_scores,
            "classifications": pae_classifications,
            "overall_quality": "good" if avg_pae < 10 else ("moderate" if avg_pae < 20 else "poor")
        }
    
    def _enrich_model_analysis(self, metadata: Dict[str, Any], models_info: Dict[str, Any]) -> None:
        """
        Add model diversity and format analysis
        
        Args:
            metadata: Metadata dictionary to enrich
            models_info: Models information
        """
        model_files = models_info.get("model_files", [])
        
        # Check available formats
        available_formats = set()
        urls_by_format = {}
        
        for model in model_files:
            urls = model.get("urls", {})
            for fmt, url in urls.items():
                if url:
                    available_formats.add(fmt)
                    if fmt not in urls_by_format:
                        urls_by_format[fmt] = []
                    urls_by_format[fmt].append(url)
        
        models_info["available_formats"] = list(available_formats)
        models_info["format_summary"] = {
            "pdb": len(urls_by_format.get("pdb", [])) > 0,
            "mmcif": len(urls_by_format.get("mmcif", [])) > 0,
            "bcif": len(urls_by_format.get("bcif", [])) > 0,
        }
        
        # Add model count info
        models_info["model_statistics"] = {
            "total_models": models_info.get("count", len(model_files)),
            "models_with_pdb": len(urls_by_format.get("pdb", [])),
            "models_with_mmcif": len(urls_by_format.get("mmcif", [])),
            "models_with_bcif": len(urls_by_format.get("bcif", [])),
        }
    
    def _enrich_uniprot_info(self, metadata: Dict[str, Any]) -> None:
        """
        Enrich UniProt information with analysis
        
        Args:
            metadata: Metadata dictionary to enrich
        """
        uniprot = metadata.get("uniprot", {})
        
        # Add sequence length categories
        seq_length = uniprot.get("sequence_length", 0)
        if seq_length > 0:
            if seq_length < 100:
                length_category = "very_small"
            elif seq_length < 300:
                length_category = "small"
            elif seq_length < 1000:
                length_category = "medium"
            else:
                length_category = "large"
            
            uniprot["sequence_length_category"] = length_category
        
        # Add gene count
        gene_names = uniprot.get("gene_names", [])
        uniprot["gene_count"] = len(gene_names)
        
        # Add information completeness score
        completeness_fields = [
            "protein_name",
            "organism",
            "function",
            "cellular_location",
            "tissue_specificity"
        ]
        
        completeness_score = sum(
            1 for field in completeness_fields
            if uniprot.get(field)
        ) / len(completeness_fields)
        
        uniprot["information_completeness"] = round(completeness_score, 2)
    
    def _classify_structure_quality(self, metadata: Dict[str, Any]) -> None:
        """
        Classify overall structure quality based on metrics
        
        Args:
            metadata: Metadata dictionary to enrich
        """
        quality_metrics = {}
        
        # Based on pLDDT if available
        if "models" in metadata and "plddt_analysis" in metadata["models"]:
            plddt_analysis = metadata["models"]["plddt_analysis"]
            avg_plddt = plddt_analysis.get("average", 0)
            
            if avg_plddt >= 90:
                quality_metrics["plddt_quality"] = "very_high"
            elif avg_plddt >= 70:
                quality_metrics["plddt_quality"] = "high"
            elif avg_plddt >= 50:
                quality_metrics["plddt_quality"] = "medium"
            else:
                quality_metrics["plddt_quality"] = "low"
        
        # Based on PAE if available
        if "models" in metadata and "pae_analysis" in metadata["models"]:
            pae_analysis = metadata["models"]["pae_analysis"]
            avg_pae = pae_analysis.get("average", float('inf'))
            
            if avg_pae < 5:
                quality_metrics["pae_quality"] = "very_good"
            elif avg_pae < 10:
                quality_metrics["pae_quality"] = "good"
            elif avg_pae < 20:
                quality_metrics["pae_quality"] = "moderate"
            else:
                quality_metrics["pae_quality"] = "poor"
        
        metadata["quality_classification"] = quality_metrics
    
    def _add_use_case_recommendations(self, metadata: Dict[str, Any]) -> None:
        """
        Add recommendations for appropriate use cases based on quality
        
        Args:
            metadata: Metadata dictionary to enrich
        """
        recommendations = []
        
        quality_class = metadata.get("quality_classification", {})
        plddt_quality = quality_class.get("plddt_quality", "")
        
        if plddt_quality == "very_high":
            recommendations.extend([
                "Suitable for drug design",
                "Suitable for detailed structural analysis",
                "Suitable for publication",
                "Suitable for experimental validation planning"
            ])
        elif plddt_quality == "high":
            recommendations.extend([
                "Suitable for protein function prediction",
                "Suitable for comparative modeling",
                "Suitable for most research applications"
            ])
        elif plddt_quality == "medium":
            recommendations.extend([
                "Suitable for domain identification",
                "Suitable for overall architecture assessment",
                "Recommend careful validation"
            ])
        else:
            recommendations.extend([
                "Use with caution",
                "Suitable only for general region identification",
                "Recommend experimental validation"
            ])
        
        metadata["use_case_recommendations"] = recommendations
    
    def _get_confidence_level(self, score: float) -> str:
        """
        Get confidence level string based on pLDDT score
        
        Args:
            score: pLDDT score
        
        Returns:
            Confidence level string
        """
        if score >= 90:
            return "Very High"
        elif score >= 70:
            return "High"
        elif score >= 50:
            return "Medium"
        else:
            return "Low"
    
    def is_applicable(self, data_type: str) -> bool:
        """
        Check if this enricher applies to the given data type
        
        Args:
            data_type: Type of data (text, structure, sequence, image)
        
        Returns:
            True if applicable for structure data
        """
        return data_type == "structure"
