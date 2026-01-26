"""
Data quality monitoring

Tracks duplicate detection, missing metadata, and embedding consistency
"""

from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
import numpy as np
from ..logger import get_logger
from .base_monitor import BaseMonitor

logger = get_logger(__name__)


class QualityMonitor(BaseMonitor):
    """Monitor data quality metrics"""
    
    def __init__(self):
        """Initialize quality monitor"""
        super().__init__(name="quality_monitor")
        
        # Track records
        self.total_records = 0
        self.records_with_errors = 0
        
        # Track duplicates (by content hash)
        self.content_hashes: Dict[str, List[str]] = defaultdict(list)
        self.duplicate_records: Set[str] = set()
        
        # Track metadata completeness
        self.metadata_fields = {
            "title": 0,
            "source": 0,
            "collection": 0,
            "date_published": 0,
            "description": 0
        }
        self.missing_metadata_records: List[Tuple[str, List[str]]] = []
        
        # Track embeddings
        self.embedding_stats = {
            "image": {"dim": 3072, "count": 0, "valid": 0},
            "text": {"dim": 384, "count": 0, "valid": 0},
            "sequence": {"dim": 384, "count": 0, "valid": 0},
            "structure": {"dim": 256, "count": 0, "valid": 0}
        }
        self.embedding_norms: Dict[str, List[float]] = defaultdict(list)
        
        # Track consistency issues
        self.consistency_issues: List[str] = []
    
    def record_ingested_record(self, record_id: str, record_dict: Dict[str, Any]):
        """
        Record an ingested record for quality checks
        
        Args:
            record_id: Record identifier
            record_dict: Record data
        """
        self.total_records += 1
        
        # Check for errors
        if record_dict.get("error"):
            self.records_with_errors += 1
        
        # Check for duplicates (simple hash of content)
        content = record_dict.get("content", "")
        if content:
            content_hash = hash(content) % (2**32)  # Simple hash
            hash_key = str(content_hash)
            
            if record_id in self.content_hashes[hash_key]:
                self.duplicate_records.add(record_id)
            else:
                self.content_hashes[hash_key].append(record_id)
        
        # Check metadata completeness
        missing_fields = []
        for field in self.metadata_fields:
            if record_dict.get(field):
                self.metadata_fields[field] += 1
            else:
                missing_fields.append(field)
        
        if missing_fields:
            self.missing_metadata_records.append((record_id, missing_fields))
    
    def record_embedding(self, data_type: str, record_id: str, embedding: np.ndarray):
        """
        Record an embedding for quality checks
        
        Args:
            data_type: Type of data (image, text, sequence, structure)
            record_id: Record identifier
            embedding: Embedding vector
        """
        if data_type not in self.embedding_stats:
            return
        
        self.embedding_stats[data_type]["count"] += 1
        
        # Check if embedding is valid
        if embedding is not None and len(embedding) > 0:
            self.embedding_stats[data_type]["valid"] += 1
            
            # Check dimension
            if len(embedding) != self.embedding_stats[data_type]["dim"]:
                self.consistency_issues.append(
                    f"Wrong dimension for {data_type} embedding {record_id}: "
                    f"expected {self.embedding_stats[data_type]['dim']}, got {len(embedding)}"
                )
            
            # Calculate norm
            norm = np.linalg.norm(embedding)
            self.embedding_norms[data_type].append(float(norm))
            
            # Check for NaN or Inf
            if np.isnan(norm) or np.isinf(norm):
                self.consistency_issues.append(
                    f"Invalid embedding norm for {data_type} record {record_id}: {norm}"
                )
    
    def collect(self) -> Dict[str, Any]:
        """Collect quality metrics"""
        # Calculate duplicate percentage
        duplicate_rate = (
            len(self.duplicate_records) / self.total_records * 100
            if self.total_records > 0
            else 0
        )
        
        # Calculate error rate
        error_rate = (
            self.records_with_errors / self.total_records * 100
            if self.total_records > 0
            else 0
        )
        
        # Calculate metadata completeness
        metadata_completeness = {}
        for field, count in self.metadata_fields.items():
            completeness = (
                count / self.total_records * 100
                if self.total_records > 0
                else 0
            )
            metadata_completeness[field] = round(completeness, 2)
        
        # Calculate embedding statistics
        embedding_stats = {}
        for data_type, stats in self.embedding_stats.items():
            if stats["count"] > 0:
                validity_rate = stats["valid"] / stats["count"] * 100
                
                # Calculate norm statistics
                norms = self.embedding_norms[data_type]
                norm_stats = {}
                if norms:
                    norm_stats = {
                        "mean_norm": round(np.mean(norms), 4),
                        "std_norm": round(np.std(norms), 4),
                        "min_norm": round(np.min(norms), 4),
                        "max_norm": round(np.max(norms), 4)
                    }
                
                embedding_stats[data_type] = {
                    "count": stats["count"],
                    "valid_count": stats["valid"],
                    "validity_rate_percent": round(validity_rate, 2),
                    "dimension": stats["dim"],
                    "norm_stats": norm_stats
                }
        
        # Average metadata completeness
        avg_metadata_completeness = (
            sum(metadata_completeness.values()) / len(metadata_completeness)
            if metadata_completeness else 0
        )
        
        return {
            "total_records": self.total_records,
            "error_rate_percent": round(error_rate, 2),
            "records_with_errors": self.records_with_errors,
            "duplicate_records": len(self.duplicate_records),
            "duplicate_rate_percent": round(duplicate_rate, 2),
            "metadata_completeness": metadata_completeness,
            "average_metadata_completeness_percent": round(avg_metadata_completeness, 2),
            "missing_metadata_records_count": len(self.missing_metadata_records),
            "embedding_statistics": embedding_stats,
            "consistency_issues_count": len(self.consistency_issues),
            "recent_consistency_issues": self.consistency_issues[-10:] if self.consistency_issues else []
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze quality metrics"""
        metrics = self.collect()
        
        issues = []
        warnings = []
        
        # Check error rate
        if metrics["error_rate_percent"] > 5:
            issues.append(f"High error rate: {metrics['error_rate_percent']}% (threshold: 5%)")
        elif metrics["error_rate_percent"] > 1:
            warnings.append(f"Elevated error rate: {metrics['error_rate_percent']}%")
        
        # Check duplicates
        if metrics["duplicate_rate_percent"] > 5:
            issues.append(f"High duplicate rate: {metrics['duplicate_rate_percent']}% (threshold: 5%)")
        elif metrics["duplicate_rate_percent"] > 1:
            warnings.append(f"Duplicate records found: {metrics['duplicate_rate_percent']}%")
        
        # Check metadata completeness
        if metrics["average_metadata_completeness_percent"] < 80:
            issues.append(
                f"Low metadata completeness: {metrics['average_metadata_completeness_percent']}% "
                f"(threshold: 80%)"
            )
        elif metrics["average_metadata_completeness_percent"] < 90:
            warnings.append(
                f"Acceptable metadata completeness: {metrics['average_metadata_completeness_percent']}%"
            )
        
        # Check embedding consistency
        if metrics["consistency_issues_count"] > 0:
            warnings.append(f"Consistency issues detected: {metrics['consistency_issues_count']}")
        
        # Check no embeddings
        if not metrics["embedding_statistics"]:
            issues.append("No embeddings recorded")
        
        return {
            "status": "HEALTHY" if not issues else "UNHEALTHY",
            "issues": issues,
            "warnings": warnings,
            "metrics": metrics
        }
    
    def get_metadata_gaps(self) -> List[Tuple[str, List[str]]]:
        """Get records with missing metadata"""
        return self.missing_metadata_records.copy()
    
    def get_duplicates(self) -> Set[str]:
        """Get duplicate record IDs"""
        return self.duplicate_records.copy()
    
    def __repr__(self) -> str:
        metrics = self.collect()
        return (
            f"QualityMonitor(total_records={metrics['total_records']}, "
            f"error_rate={metrics['error_rate_percent']}%, "
            f"duplicates={metrics['duplicate_records']})"
        )
