#!/usr/bin/env python3
"""
Test monitoring system with simulated pipeline operations
"""

import sys
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.monitoring import MonitoringDashboard
from datetime import datetime


def simulate_ingestion_events(dashboard: MonitoringDashboard):
    """Simulate various ingestion events"""
    print("\n" + "="*70)
    print("SIMULATING INGESTION EVENTS")
    print("="*70 + "\n")
    
    # Successful ingestions
    sources = ["arxiv", "biorxiv", "local_files", "pdb"]
    successes = [95, 90, 98, 100]
    failures = [5, 10, 2, 0]
    
    for source, success_count, failure_count in zip(sources, successes, failures):
        for _ in range(success_count):
            dashboard.record_ingest_attempt(source, success=True)
        
        for i in range(failure_count):
            errors = [
                "Network timeout",
                "Invalid format",
                "File not found",
                "Rate limit exceeded",
                "Authentication failed"
            ]
            dashboard.record_ingest_attempt(source, success=False, error=errors[i % len(errors)])
    
    print("✓ Recorded ingestion attempts across 4 sources")
    print(f"  - Total attempts: {sum(successes) + sum(failures)}")
    print(f"  - Total successful: {sum(successes)}")
    print(f"  - Total failed: {sum(failures)}")


def simulate_ingested_records(dashboard: MonitoringDashboard):
    """Simulate ingested records with varying quality"""
    print("\n" + "="*70)
    print("SIMULATING INGESTED RECORDS")
    print("="*70 + "\n")
    
    sources = ["arxiv", "biorxiv", "local_files"]
    data_types = ["text", "sequence", "image", "structure"]
    collections = ["papers", "sequences", "images", "structures"]
    
    record_id = 1
    for source in sources:
        for data_type, collection in zip(data_types, collections):
            for i in range(25):  # 25 records per combination
                # Occasionally add missing metadata
                has_title = np.random.random() > 0.05
                has_description = np.random.random() > 0.10
                
                record_dict = {
                    "id": f"rec-{record_id}",
                    "data_type": data_type,
                    "source": source,
                    "collection": collection,
                    "title": f"Sample {data_type} {i}" if has_title else None,
                    "description": f"Description {i}" if has_description else None,
                    "error": None
                }
                
                dashboard.record_ingested_record(
                    f"rec-{record_id}",
                    data_type,
                    source,
                    record_dict
                )
                record_id += 1
    
    print(f"✓ Recorded {record_id - 1} ingested records")
    print(f"  - Modalities: {len(data_types)}")
    print(f"  - Sources: {len(sources)}")
    print(f"  - Collections: {len(collections)}")


def simulate_embeddings(dashboard: MonitoringDashboard):
    """Simulate embeddings with varying quality"""
    print("\n" + "="*70)
    print("SIMULATING EMBEDDINGS")
    print("="*70 + "\n")
    
    embedding_dims = {
        "text": 384,
        "sequence": 384,
        "image": 3072,
        "structure": 256
    }
    
    total_embeddings = 0
    
    for data_type, dim in embedding_dims.items():
        for i in range(25):
            record_id = f"rec-{total_embeddings + 1}"
            
            # Create valid embedding with random values
            embedding = np.random.randn(dim) * 0.5 + 0.5
            
            # Occasionally add invalid embedding
            if np.random.random() > 0.98:
                embedding = np.full(dim, np.nan)
            
            dashboard.record_embedding(data_type, record_id, embedding)
            total_embeddings += 1
    
    print(f"✓ Recorded {total_embeddings} embeddings")
    for data_type, dim in embedding_dims.items():
        print(f"  - {data_type}: {dim}-dim ({25} vectors)")


def main():
    """Run monitoring system test"""
    print("\n" + "="*70)
    print("PIPELINE MONITORING SYSTEM TEST")
    print("="*70)
    
    dashboard = MonitoringDashboard()
    
    # Simulate operations
    simulate_ingestion_events(dashboard)
    simulate_ingested_records(dashboard)
    simulate_embeddings(dashboard)
    
    # Get reports
    print("\n" + "="*70)
    print("MONITORING REPORTS")
    print("="*70)
    
    health_report = dashboard.get_health_report()
    quality_report = dashboard.get_quality_report()
    balance_report = dashboard.get_balance_report()
    
    # Print health report
    print("\n📊 HEALTH REPORT")
    print("-" * 70)
    print(f"Status: {health_report['status']}")
    print(f"Success Rate: {health_report['metrics']['success_rate_percent']}%")
    print(f"Total Attempts: {health_report['metrics']['total_attempts']}")
    print(f"Active Sources: {health_report['metrics']['active_sources']}")
    if health_report['issues']:
        print(f"Issues: {health_report['issues']}")
    if health_report['warnings']:
        print(f"Warnings: {health_report['warnings']}")
    
    # Print quality report
    print("\n📊 QUALITY REPORT")
    print("-" * 70)
    print(f"Status: {quality_report['status']}")
    print(f"Total Records: {quality_report['metrics']['total_records']}")
    print(f"Error Rate: {quality_report['metrics']['error_rate_percent']}%")
    print(f"Duplicate Rate: {quality_report['metrics']['duplicate_rate_percent']}%")
    print(f"Metadata Completeness: {quality_report['metrics']['average_metadata_completeness_percent']}%")
    
    embedding_stats = quality_report['metrics'].get('embedding_statistics', {})
    if embedding_stats:
        print("Embedding Validity:")
        for data_type, stats in embedding_stats.items():
            print(f"  - {data_type}: {stats['validity_rate_percent']}%")
    
    if quality_report['issues']:
        print(f"Issues: {quality_report['issues']}")
    if quality_report['warnings']:
        print(f"Warnings: {quality_report['warnings']}")
    
    # Print balance report
    print("\n📊 BALANCE REPORT")
    print("-" * 70)
    print(f"Status: {balance_report['status']}")
    print(f"Total Records: {balance_report['metrics']['total_records']}")
    print(f"Gini Coefficient: {balance_report['metrics']['gini_coefficient']}")
    
    if balance_report['metrics']['modality_distribution']:
        print("Modality Distribution:")
        for modality, dist in balance_report['metrics']['modality_distribution'].items():
            print(f"  - {modality}: {dist['count']} ({dist['percentage']}%)")
    
    if balance_report['issues']:
        print(f"Issues: {balance_report['issues']}")
    if balance_report['warnings']:
        print(f"Warnings: {balance_report['warnings']}")
    
    # Print comprehensive dashboard
    print("\n" + "="*70)
    print("COMPREHENSIVE MONITORING DASHBOARD")
    print("="*70)
    print(dashboard.print_report(include_metrics=True))
    
    # Get comprehensive report
    comprehensive = dashboard.get_comprehensive_report()
    print("\n📈 SUMMARY")
    print("-" * 70)
    print(f"Overall Status: {comprehensive['overall_status']}")
    print(f"Uptime: {comprehensive['uptime_hours']} hours")
    print(f"Total Issues: {comprehensive['total_issues']}")
    print(f"Total Warnings: {comprehensive['total_warnings']}")
    
    # Test snapshot history
    print("\n📋 TAKING SNAPSHOTS")
    print("-" * 70)
    for i in range(3):
        dashboard.health_monitor.take_snapshot()
        dashboard.quality_monitor.take_snapshot()
        dashboard.balance_monitor.take_snapshot()
        print(f"✓ Snapshot {i+1} taken")
    
    history_len = len(dashboard.health_monitor.get_history())
    print(f"✓ History depth: {history_len} snapshots per monitor")
    
    print("\n" + "="*70)
    print("TEST COMPLETE ✓")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
