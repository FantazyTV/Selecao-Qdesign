"""
Modality balance monitoring

Tracks balance of different data modalities (images, text, sequences, structures)
"""

from typing import Dict, Any, List
from collections import defaultdict
from ..logger import get_logger
from .base_monitor import BaseMonitor

logger = get_logger(__name__)


class BalanceMonitor(BaseMonitor):
    """Monitor modality balance and distribution"""
    
    def __init__(self):
        """Initialize balance monitor"""
        super().__init__(name="balance_monitor")
        
        # Track counts by modality
        self.modality_counts: Dict[str, int] = defaultdict(int)
        
        # Track source distribution
        self.source_distribution: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Track collection distribution
        self.collection_distribution: Dict[str, int] = defaultdict(int)
        
        # Target balance (for alerts)
        self.target_balance = {
            "image": 0.25,
            "text": 0.25,
            "sequence": 0.25,
            "structure": 0.25
        }
        
        # Tolerance for imbalance (percent)
        self.imbalance_tolerance = 10  # +/- 10% from target
    
    def record_data(self, data_type: str, source: str = "unknown", collection: str = "unknown"):
        """
        Record data point for balance tracking
        
        Args:
            data_type: Type of data (image, text, sequence, structure)
            source: Source of data (arxiv, biorxiv, local, etc)
            collection: Collection name
        """
        self.modality_counts[data_type] += 1
        self.source_distribution[data_type][source] += 1
        self.collection_distribution[collection] += 1
    
    def collect(self) -> Dict[str, Any]:
        """Collect balance metrics"""
        total_records = sum(self.modality_counts.values())
        
        # Calculate modality percentages
        modality_distribution = {}
        if total_records > 0:
            for modality, count in self.modality_counts.items():
                percentage = count / total_records * 100
                modality_distribution[modality] = {
                    "count": count,
                    "percentage": round(percentage, 2)
                }
        
        # Identify imbalanced modalities
        imbalanced_modalities = {}
        if total_records > 0:
            for modality in self.target_balance.keys():
                current_percentage = modality_distribution.get(modality, {}).get("percentage", 0)
                target_percentage = self.target_balance[modality] * 100
                difference = current_percentage - target_percentage
                
                is_imbalanced = abs(difference) > self.imbalance_tolerance
                imbalanced_modalities[modality] = {
                    "current_percent": round(current_percentage, 2),
                    "target_percent": round(target_percentage, 2),
                    "difference_percent": round(difference, 2),
                    "is_imbalanced": is_imbalanced
                }
        
        # Calculate source diversity
        source_diversity = {}
        for modality, sources in self.source_distribution.items():
            source_diversity[modality] = {
                "sources": len(sources),
                "distribution": dict(sources)
            }
        
        # Calculate Gini coefficient for distribution imbalance (0=perfect balance, 1=perfect imbalance)
        gini = self._calculate_gini(list(self.modality_counts.values())) if total_records > 0 else 0
        
        return {
            "total_records": total_records,
            "modality_distribution": modality_distribution,
            "imbalance_analysis": imbalanced_modalities,
            "source_diversity": source_diversity,
            "collection_distribution": dict(self.collection_distribution),
            "gini_coefficient": round(gini, 4),
            "is_balanced": not any(m["is_imbalanced"] for m in imbalanced_modalities.values())
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze balance metrics"""
        metrics = self.collect()
        
        issues = []
        warnings = []
        
        # Check if balanced
        imbalance_analysis = metrics["imbalance_analysis"]
        for modality, analysis in imbalance_analysis.items():
            if analysis["is_imbalanced"]:
                diff = analysis["difference_percent"]
                if diff > self.imbalance_tolerance:
                    issues.append(
                        f"Over-represented modality '{modality}': "
                        f"{analysis['current_percent']}% (expected ~{analysis['target_percent']}%)"
                    )
                elif diff < -self.imbalance_tolerance:
                    issues.append(
                        f"Under-represented modality '{modality}': "
                        f"{analysis['current_percent']}% (expected ~{analysis['target_percent']}%)"
                    )
        
        # Check Gini coefficient
        gini = metrics["gini_coefficient"]
        if gini > 0.3:
            warnings.append(f"High distribution imbalance (Gini: {gini})")
        elif gini > 0.15:
            warnings.append(f"Some distribution imbalance (Gini: {gini})")
        
        # Check source diversity
        for modality, diversity in metrics["source_diversity"].items():
            if diversity["sources"] == 0:
                issues.append(f"No data sources for modality '{modality}'")
            elif diversity["sources"] == 1:
                warnings.append(f"Single source for modality '{modality}'")
        
        return {
            "status": "BALANCED" if not issues else "IMBALANCED",
            "issues": issues,
            "warnings": warnings,
            "metrics": metrics
        }
    
    def get_modality_summary(self) -> Dict[str, int]:
        """Get count of each modality"""
        return dict(self.modality_counts)
    
    def get_modality_percentages(self) -> Dict[str, float]:
        """Get percentage distribution of modalities"""
        total = sum(self.modality_counts.values())
        if total == 0:
            return {}
        
        return {
            modality: round(count / total * 100, 2)
            for modality, count in self.modality_counts.items()
        }
    
    @staticmethod
    def _calculate_gini(values: List[int]) -> float:
        """
        Calculate Gini coefficient for distribution
        
        0 = perfect equality, 1 = perfect inequality
        
        Args:
            values: List of counts
        
        Returns:
            Gini coefficient
        """
        if not values or len(values) < 2:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Gini = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
        cumsum = sum((i + 1) * val for i, val in enumerate(sorted_values))
        total = sum(sorted_values)
        
        if total == 0:
            return 0.0
        
        gini = (2 * cumsum) / (n * total) - (n + 1) / n
        return max(0, gini)  # Gini should be between 0 and 1
    
    def __repr__(self) -> str:
        metrics = self.collect()
        return (
            f"BalanceMonitor(total_records={metrics['total_records']}, "
            f"modalities={len(metrics['modality_distribution'])}, "
            f"gini={metrics['gini_coefficient']})"
        )
