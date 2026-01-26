#!/usr/bin/env python3
"""
Automated data downloader for QDesign pipeline
Downloads papers, sequences, structures, and images from various sources
Usage: python download_data.py [--all|--text|--sequence|--structure|--image] [--limit 10]
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import List, Optional
import time
from urllib.parse import urljoin

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "Data"


class DataDownloader:
    """Automated data downloader for QDesign pipeline"""
    
    def __init__(self, data_dir: Path = DATA_DIR, verbose: bool = True):
        self.data_dir = data_dir
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QDesign-DataCollector/1.0'
        })
        self._create_directories()
    
    def _create_directories(self):
        """Create all necessary data directories"""
        dirs = [
            self.data_dir / "text" / "papers",
            self.data_dir / "text" / "documents",
            self.data_dir / "sequences" / "fasta",
            self.data_dir / "structures" / "pdb",
            self.data_dir / "images" / "microscopy",
            self.data_dir / "images" / "diagrams",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        if self.verbose:
            print(f" Directories ready at {self.data_dir}")
    
    def _log(self, message: str):
        """Log with optional verbose mode"""
        if self.verbose:
            print(message)
    
    def _download_file(self, url: str, filepath: Path, timeout: int = 30) -> bool:
        """Download a file from URL"""
        try:
            if filepath.exists():
                self._log(f"  ⊘ Already exists: {filepath.name}")
                return True
            
            self._log(f"  Downloading: {filepath.name}...", end=" ")
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            size_mb = filepath.stat().st_size / (1024 * 1024)
            self._log(f" ({size_mb:.1f} MB)")
            return True
            
        except Exception as e:
            self._log(f"✗ Failed: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
    
    def _log(self, message: str, end: str = "\n"):
        """Log with optional verbose mode"""
        if self.verbose:
            print(message, end=end)
            sys.stdout.flush()
    
    # ===== TEXT/PAPERS =====
    def download_arxiv_papers(self, query: str = "protein design", limit: int = 5) -> int:
        """Download papers from arXiv"""
        self._log(f"\n📄 Downloading {limit} arXiv papers (query: '{query}')...")
        
        papers_dir = self.data_dir / "text" / "papers"
        count = 0
        
        # ArXiv API
        base_url = "http://export.arxiv.org/api/query?"
        params = f"search_query=cat:q-bio AND all:{query}&start=0&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
        
        try:
            response = self.session.get(f"{base_url}{params}", timeout=10)
            response.raise_for_status()
            
            # Parse XML response (simple regex parsing)
            import re
            pdf_urls = re.findall(r'href="(https://arxiv.org/pdf/[^"]+)"', response.text)
            
            for i, pdf_url in enumerate(pdf_urls[:limit], 1):
                arxiv_id = pdf_url.split('/pdf/')[-1].replace('.pdf', '').replace('/', '_')
                filepath = papers_dir / f"arxiv_{arxiv_id}.pdf"
                
                if self._download_file(pdf_url, filepath):
                    count += 1
                time.sleep(0.5)  # Rate limiting
            
            self._log(f" Downloaded {count}/{limit} arXiv papers")
            return count
            
        except Exception as e:
            self._log(f"✗ ArXiv download failed: {e}")
            return count
    
    # ===== SEQUENCES =====
    def download_uniprot_sequences(self, limit: int = 50) -> int:
        """Download protein sequences from UniProt"""
        self._log(f"\n Downloading {limit} UniProt sequences...")
        
        fasta_dir = self.data_dir / "sequences" / "fasta"
        count = 0
        
        try:
            # Try the search API, but if it fails, just note that specific downloads work better
            from urllib.parse import urlencode
            
            # Build proper query
            query_params = {
                'query': 'reviewed:true AND organism_id:9606 AND length:[100 TO 500]',
                'format': 'fasta',
                'size': limit
            }
            
            url = f"https://www.uniprot.org/uniprotkb/search?" + urlencode(query_params)
            
            try:
                response = requests.get(url, timeout=30, headers={'User-Agent': 'QDesign'})
                response.raise_for_status()
                
                # Save as single file with multiple sequences
                filepath = fasta_dir / "uniprot_human_proteins.fasta"
                with open(filepath, 'w') as f:
                    f.write(response.text)
                
                # Count sequences
                seq_count = response.text.count('>')
                self._log(f" Downloaded {seq_count} sequences ({filepath.stat().st_size / 1024:.1f} KB)")
                return seq_count
            except Exception as e:
                self._log(f"⚠  Batch download unavailable ({e}), using individual sequences instead")
                return 0
            
        except Exception as e:
            self._log(f"✗ UniProt download failed: {e}")
            return count
    
    def download_specific_uniprot_proteins(self, protein_ids: List[str]) -> int:
        """Download specific UniProt proteins by ID"""
        self._log(f"\n Downloading {len(protein_ids)} specific UniProt proteins...")
        
        fasta_dir = self.data_dir / "sequences" / "fasta"
        count = 0
        
        proteins_info = {
            'P42212': ('gfp.fasta', 'Green Fluorescent Protein'),
            'P69905': ('hemoglobin_beta.fasta', 'Hemoglobin'),
            'P61626': ('lysozyme.fasta', 'Lysozyme'),
            'P01308': ('insulin.fasta', 'Insulin'),
            'P01857': ('antibody.fasta', 'Antibody IgG'),
        }
        
        for uniprot_id in protein_ids:
            if uniprot_id not in proteins_info:
                continue
            
            filename, name = proteins_info[uniprot_id]
            filepath = fasta_dir / filename
            url = f"https://www.uniprot.org/uniprotkb/{uniprot_id}.fasta"
            
            self._log(f"  {name}:", end=" ")
            if self._download_file(url, filepath):
                count += 1
            time.sleep(0.3)  # Rate limiting
        
        self._log(f" Downloaded {count} proteins")
        return count
    
    # ===== STRUCTURES =====
    def download_pdb_structures(self, pdb_ids: List[str]) -> int:
        """Download protein structures from PDB"""
        self._log(f"\n Downloading {len(pdb_ids)} PDB structures...")
        
        pdb_dir = self.data_dir / "structures" / "pdb"
        count = 0
        
        pdb_info = {
            '1GFP': 'GFP - Green Fluorescent Protein',
            '1HBA': 'Hemoglobin A',
            '1MBN': 'Myoglobin',
            '1LYZ': 'Lysozyme',
            '2AQ4': 'DNA Polymerase',
            '6VSB': 'SARS-CoV-2 Spike Protein',
            '4ZT0': 'Cas9 CRISPR',
            '1HZH': 'Antibody IgG1',
        }
        
        for pdb_id in pdb_ids:
            if pdb_id not in pdb_info:
                continue
            
            name = pdb_info[pdb_id]
            filepath = pdb_dir / f"{pdb_id.lower()}.pdb"
            url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
            
            self._log(f"  {name}:", end=" ")
            if self._download_file(url, filepath):
                count += 1
            time.sleep(0.3)  # Rate limiting
        
        self._log(f" Downloaded {count} structures")
        return count
    
    def download_alphafold_structures(self, uniprot_ids: List[str]) -> int:
        """Download AlphaFold predicted structures"""
        self._log(f"\n Downloading {len(uniprot_ids)} AlphaFold structures...")
        
        pdb_dir = self.data_dir / "structures" / "pdb"
        count = 0
        
        alphafold_info = {
            'P42212': 'GFP (AlphaFold)',
            'P61626': 'Lysozyme (AlphaFold)',
            'P69905': 'Hemoglobin (AlphaFold)',
        }
        
        for uniprot_id in uniprot_ids:
            if uniprot_id not in alphafold_info:
                continue
            
            name = alphafold_info[uniprot_id]
            filepath = pdb_dir / f"af_{uniprot_id.lower()}.pdb"
            url = f"https://alphafolddb.uniprot.org/files/AF-{uniprot_id}-F1-model_v4.pdb"
            
            self._log(f"  {name}:", end=" ")
            if self._download_file(url, filepath):
                count += 1
            time.sleep(0.5)  # Rate limiting
        
        self._log(f" Downloaded {count} AlphaFold structures")
        return count
    
    # ===== IMAGES =====
    def download_wikimedia_images(self) -> int:
        """Download images from Wikimedia Commons"""
        self._log(f"\n  Downloading sample images...")
        
        # Note: Wikimedia is rate-limiting, so we provide downloadable links
        # Users can manually download if needed, but we'll try a few direct sources
        images = [
            # Direct links to actual image files (no thumbnails)
            ('diagrams', 'https://en.wikipedia.org/wiki/Special:FilePath/Protein_structure.jpg', 'protein_structure.jpg'),
        ]
        
        count = 0
        for img_type, url, filename in images:
            img_dir = self.data_dir / "images" / img_type
            filepath = img_dir / filename
            
            self._log(f"  {filename}:", end=" ")
            if self._download_file(url, filepath):
                count += 1
            time.sleep(0.3)
        
        if count == 0:
            self._log("\n  ℹ  Wikimedia is rate-limiting. To download images:")
            self._log("    - Protein diagram: https://commons.wikimedia.org/wiki/File:Protein_structure.svg")
            self._log("    - Cell images: https://commons.wikimedia.org/wiki/Category:Eukaryotic_cells")
            self._log("    - Save images to Data/images/diagrams/ or Data/images/microscopy/")
        
        self._log(f" Images section complete (manually download if needed)")
        return count
    
    # ===== MAIN DOWNLOAD FUNCTIONS =====
    def download_text_data(self, arxiv_query: str = "protein design", limit: int = 5):
        """Download all text data"""
        self._log("\n" + "="*60)
        self._log("📚 DOWNLOADING TEXT DATA")
        self._log("="*60)
        
        total = 0
        total += self.download_arxiv_papers(arxiv_query, limit)
        return total
    
    def download_sequence_data(self, limit: int = 50, include_specific: bool = True):
        """Download all sequence data"""
        self._log("\n" + "="*60)
        self._log(" DOWNLOADING SEQUENCE DATA")
        self._log("="*60)
        
        total = 0
        total += self.download_uniprot_sequences(limit)
        
        if include_specific:
            specific_ids = ['P42212', 'P69905', 'P61626', 'P01308', 'P01857']
            total += self.download_specific_uniprot_proteins(specific_ids)
        
        return total
    
    def download_structure_data(self):
        """Download all structure data"""
        self._log("\n" + "="*60)
        self._log("  DOWNLOADING STRUCTURE DATA")
        self._log("="*60)
        
        total = 0
        pdb_ids = ['1GFP', '1HBA', '1MBN', '1LYZ', '2AQ4', '6VSB', '4ZT0', '1HZH']
        total += self.download_pdb_structures(pdb_ids)
        
        af_ids = ['P42212', 'P61626', 'P69905']
        total += self.download_alphafold_structures(af_ids)
        
        return total
    
    def download_image_data(self):
        """Download all image data"""
        self._log("\n" + "="*60)
        self._log("  DOWNLOADING IMAGE DATA")
        self._log("="*60)
        
        total = 0
        total += self.download_wikimedia_images()
        return total
    
    def download_all(self, arxiv_limit: int = 5, seq_limit: int = 50):
        """Download all data"""
        self._log("\n" + "="*70)
        self._log(" QDesign Data Downloader - Downloading All Data")
        self._log("="*70)
        
        total = 0
        
        try:
            total += self.download_text_data(limit=arxiv_limit)
            total += self.download_sequence_data(limit=seq_limit)
            total += self.download_structure_data()
            total += self.download_image_data()
            
            self._log("\n" + "="*70)
            self._log(f" Download Complete! Total items: {total}")
            self._log(f" Data saved to: {self.data_dir}")
            self._log("="*70)
            return total
            
        except Exception as e:
            self._log(f"\n Download failed: {e}")
            return total


def main():
    parser = argparse.ArgumentParser(
        description="Automated data downloader for QDesign pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_data.py --all                    # Download everything
  python download_data.py --text --limit 10        # Download 10 arXiv papers
  python download_data.py --sequence --limit 100   # Download 100 sequences
  python download_data.py --structure              # Download all structures
  python download_data.py --image                  # Download all images
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Download all data types')
    parser.add_argument('--text', action='store_true', help='Download text/papers')
    parser.add_argument('--sequence', action='store_true', help='Download protein sequences')
    parser.add_argument('--structure', action='store_true', help='Download protein structures')
    parser.add_argument('--image', action='store_true', help='Download images')
    parser.add_argument('--limit', type=int, default=5, help='Number of items to download (default: 5)')
    parser.add_argument('--query', default='protein design', help='Search query for arXiv (default: protein design)')
    parser.add_argument('--data-dir', type=Path, default=DATA_DIR, help='Data directory path')
    parser.add_argument('--no-verbose', action='store_true', help='Disable verbose output')
    
    args = parser.parse_args()
    
    # If no specific type selected, download all
    if not any([args.all, args.text, args.sequence, args.structure, args.image]):
        args.all = True
    
    downloader = DataDownloader(args.data_dir, verbose=not args.no_verbose)
    
    try:
        if args.all:
            downloader.download_all(arxiv_limit=args.limit, seq_limit=args.limit)
        else:
            if args.text:
                downloader.download_text_data(args.query, args.limit)
            if args.sequence:
                downloader.download_sequence_data(args.limit)
            if args.structure:
                downloader.download_structure_data()
            if args.image:
                downloader.download_image_data()
    
    except KeyboardInterrupt:
        print("\n\n  Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
