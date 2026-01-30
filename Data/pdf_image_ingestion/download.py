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
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup

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
            print(f"✅ Directories ready at {self.data_dir}")
    
    def _log(self, message: str, end: str = "\n"):
        """Log with optional verbose mode"""
        if self.verbose:
            print(message, end=end)
            sys.stdout.flush()
    
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
            self._log(f"✓ ({size_mb:.1f} MB)")
            return True
            
        except Exception as e:
            self._log(f"✗ Failed: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
    
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
            
            self._log(f"✅ Downloaded {count}/{limit} arXiv papers")
            return count
            
        except Exception as e:
            self._log(f"✗ ArXiv download failed: {e}")
            return count
    
    def download_biorxiv_papers(self, limit: int = 5) -> int:
        """Download papers from bioRxiv (preprint server)"""
        self._log(f"\n📄 Downloading {limit} bioRxiv papers...")
        
        papers_dir = self.data_dir / "text" / "papers"
        count = 0
        
        # Note: bioRxiv doesn't have a simple API, so we provide direct links
        biorxiv_samples = [
            ('https://www.biorxiv.org/content/10.1101/2024.01.01.000001v1.full.pdf', 'biorxiv_protein_sample_1.pdf'),
            # Add more as needed
        ]
        
        for url, filename in biorxiv_samples[:limit]:
            filepath = papers_dir / filename
            if self._download_file(url, filepath):
                count += 1
            time.sleep(1)  # Rate limiting
        
        self._log(f"✅ Downloaded {count} bioRxiv papers")
        return count
    
    # ===== SEQUENCES =====
    def download_uniprot_sequences(self, limit: int = 50) -> int:
        """Download protein sequences from UniProt"""
        self._log(f"\n🧬 Downloading {limit} UniProt sequences...")
        
        fasta_dir = self.data_dir / "sequences" / "fasta"
        count = 0
        
        try:
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
                self._log(f"✅ Downloaded {seq_count} sequences ({filepath.stat().st_size / 1024:.1f} KB)")
                return seq_count
            except Exception as e:
                self._log(f"⚠️  Batch download unavailable ({e}), using individual sequences instead")
                return 0
            
        except Exception as e:
            self._log(f"✗ UniProt download failed: {e}")
            return count
    
    def download_specific_uniprot_proteins(self, protein_ids: List[str]) -> int:
        """Download specific UniProt proteins by ID"""
        self._log(f"\n🧬 Downloading {len(protein_ids)} specific UniProt proteins...")
        
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
        
        self._log(f"✅ Downloaded {count} proteins")
        return count
    
    # ===== STRUCTURES =====
    def download_pdb_structures(self, pdb_ids: List[str]) -> int:
        """Download protein structures from PDB"""
        self._log(f"\n🔬 Downloading {len(pdb_ids)} PDB structures...")
        
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
        
        self._log(f"✅ Downloaded {count} structures")
        return count
    
    def download_alphafold_structures(self, uniprot_ids: List[str]) -> int:
        """Download AlphaFold predicted structures"""
        self._log(f"\n🔬 Downloading {len(uniprot_ids)} AlphaFold structures...")
        
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
            url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
            
            self._log(f"  {name}:", end=" ")
            if self._download_file(url, filepath):
                count += 1
            time.sleep(0.5)  # Rate limiting
        
        self._log(f"✅ Downloaded {count} AlphaFold structures")
        return count
    
    # ===== IMAGES =====
    def _scrape_wikimedia_images(self, search_term: str, limit: int = 10) -> List[tuple]:
        """Scrape Wikimedia Commons for images based on search term"""
        images = []
        
        try:
            # Use Wikimedia Commons search
            search_url = f"https://commons.wikimedia.org/w/index.php?search={quote(search_term)}&title=Special:MediaSearch&go=Go&type=image"
            
            self._log(f"  Searching Wikimedia for '{search_term}'...")
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find image results - Wikimedia uses specific classes for search results
            # Look for image thumbnails in search results
            img_containers = soup.find_all('div', class_='sdms-search-results__list-item')
            
            if not img_containers:
                # Try alternative selectors
                img_containers = soup.find_all('a', class_='sdms-image-result')
            
            for container in img_containers[:limit]:
                try:
                    # Get the link to the file page
                    link = container.get('href') or container.find('a', href=True)
                    if link and isinstance(link, str):
                        file_url = link
                    elif link:
                        file_url = link.get('href')
                    else:
                        continue
                    
                    if not file_url.startswith('http'):
                        file_url = 'https://commons.wikimedia.org' + file_url
                    
                    # Visit the file page to get the actual image URL
                    file_response = self.session.get(file_url, timeout=10)
                    file_soup = BeautifulSoup(file_response.content, 'html.parser')
                    
                    # Find the original file link
                    original_file = file_soup.find('a', class_='internal') or file_soup.find('div', class_='fullImageLink')
                    if original_file:
                        img_url = original_file.get('href')
                        if img_url and not img_url.startswith('http'):
                            img_url = 'https:' + img_url
                        
                        # Get filename from URL
                        filename = img_url.split('/')[-1].split('?')[0]
                        
                        # Clean filename
                        filename = filename.replace('%20', '_').replace('%28', '(').replace('%29', ')')
                        
                        images.append((img_url, filename))
                        
                        if len(images) >= limit:
                            break
                    
                    time.sleep(0.5)  # Rate limiting between file page requests
                    
                except Exception as e:
                    self._log(f"    ⚠️  Error parsing result: {e}")
                    continue
            
            if not images:
                self._log(f"    ⚠️  No images found via scraping, trying API fallback...")
                # Fallback to Wikimedia API
                api_url = "https://commons.wikimedia.org/w/api.php"
                params = {
                    'action': 'query',
                    'format': 'json',
                    'list': 'search',
                    'srsearch': search_term,
                    'srnamespace': '6',  # File namespace
                    'srlimit': limit
                }
                
                api_response = self.session.get(api_url, params=params, timeout=10)
                api_data = api_response.json()
                
                for result in api_data.get('query', {}).get('search', [])[:limit]:
                    title = result['title'].replace('File:', '')
                    # Get file URL via imageinfo API
                    img_params = {
                        'action': 'query',
                        'format': 'json',
                        'titles': f"File:{title}",
                        'prop': 'imageinfo',
                        'iiprop': 'url'
                    }
                    img_response = self.session.get(api_url, params=img_params, timeout=10)
                    img_data = img_response.json()
                    
                    pages = img_data.get('query', {}).get('pages', {})
                    for page in pages.values():
                        imageinfo = page.get('imageinfo', [])
                        if imageinfo:
                            img_url = imageinfo[0].get('url')
                            if img_url:
                                filename = title.replace(' ', '_')
                                images.append((img_url, filename))
                                break
                    
                    time.sleep(0.3)
        
        except Exception as e:
            self._log(f"    ✗ Wikimedia scraping failed: {e}")
        
        return images
    
    def download_protein_images(self, limit: int = 10) -> int:
        """Download protein and biology images from Wikimedia Commons via scraping"""
        self._log(f"\n🖼️  Downloading {limit} protein/biology images from Wikimedia...")
        
        diagrams_dir = self.data_dir / "images" / "diagrams"
        microscopy_dir = self.data_dir / "images" / "microscopy"
        count = 0
        
        # Search terms for different types of images
        search_queries = [
            ('protein structure', 'diagrams', limit // 2),
            ('microscopy', 'microscopy', limit // 2),
        ]
        
        for search_term, img_type, search_limit in search_queries:
            self._log(f"\n  Searching for '{search_term}' images...")
            
            # Scrape images from Wikimedia
            images = self._scrape_wikimedia_images(search_term, search_limit)
            
            if images:
                self._log(f"  Found {len(images)} images")
                
                img_dir = diagrams_dir if img_type == 'diagrams' else microscopy_dir
                
                for img_url, original_filename in images:
                    # Create a clean filename
                    safe_filename = original_filename[:100]  # Limit length
                    filepath = img_dir / safe_filename
                    
                    if self._download_file(img_url, filepath, timeout=20):
                        count += 1
                    
                    time.sleep(0.5)  # Rate limiting
        
        if count == 0:
            self._log("\n  ℹ️  Image download failed. Manual download links:")
            self._log("    - Protein diagrams: https://commons.wikimedia.org/wiki/Category:Protein_structure")
            self._log("    - Cell images: https://commons.wikimedia.org/wiki/Category:Cells_in_culture")
            self._log("    - Save images to Data/images/diagrams/ or Data/images/microscopy/")
        else:
            self._log(f"\n✅ Downloaded {count} images from Wikimedia Commons")
        
        return count
    
    def download_pdb_images(self, pdb_ids: List[str]) -> int:
        """Download PDB structure images (rendered previews)"""
        self._log(f"\n🖼️  Downloading {len(pdb_ids)} PDB structure images...")
        
        diagrams_dir = self.data_dir / "images" / "diagrams"
        count = 0
        
        for pdb_id in pdb_ids:
            # PDB provides preview images
            filepath = diagrams_dir / f"{pdb_id.lower()}_structure.png"
            url = f"https://cdn.rcsb.org/images/structures/{pdb_id.lower()}_assembly-1.jpeg"
            
            self._log(f"  {pdb_id}:", end=" ")
            if self._download_file(url, filepath, timeout=15):
                count += 1
            time.sleep(0.3)
        
        self._log(f"✅ Downloaded {count} PDB images")
        return count
    
    # ===== MAIN DOWNLOAD FUNCTIONS =====
    def download_text_data(self, arxiv_query: str = "protein design", limit: int = 5):
        """Download all text data"""
        self._log("\n" + "="*70)
        self._log("📚 DOWNLOADING TEXT DATA")
        self._log("="*70)
        
        total = 0
        total += self.download_arxiv_papers(arxiv_query, limit)
        return total
    
    def download_sequence_data(self, limit: int = 50, include_specific: bool = True):
        """Download all sequence data"""
        self._log("\n" + "="*70)
        self._log("🧬 DOWNLOADING SEQUENCE DATA")
        self._log("="*70)
        
        total = 0
        total += self.download_uniprot_sequences(limit)
        
        if include_specific:
            specific_ids = ['P42212', 'P69905', 'P61626', 'P01308', 'P01857']
            total += self.download_specific_uniprot_proteins(specific_ids)
        
        return total
    
    def download_structure_data(self):
        """Download all structure data"""
        self._log("\n" + "="*70)
        self._log("🔬 DOWNLOADING STRUCTURE DATA")
        self._log("="*70)
        
        total = 0
        pdb_ids = ['1GFP', '1HBA', '1MBN', '1LYZ', '2AQ4', '6VSB', '4ZT0', '1HZH']
        total += self.download_pdb_structures(pdb_ids)
        
        af_ids = ['P42212', 'P61626', 'P69905']
        total += self.download_alphafold_structures(af_ids)
        
        return total
    
    def download_image_data(self, limit: int = 10, include_pdb_images: bool = True):
        """Download all image data"""
        self._log("\n" + "="*70)
        self._log("🖼️  DOWNLOADING IMAGE DATA")
        self._log("="*70)
        
        total = 0
        total += self.download_protein_images(limit)
        
        if include_pdb_images:
            pdb_ids = ['1GFP', '1HBA', '1LYZ', '6VSB']
            total += self.download_pdb_images(pdb_ids)
        
        return total
    
    def download_all(self, arxiv_limit: int = 20, seq_limit: int = 50, image_limit: int = 20):
        """Download all data"""
        self._log("\n" + "="*70)
        self._log("🚀 QDesign Data Downloader - Downloading All Data")
        self._log("="*70)
        
        total = 0
        
        try:
            total += self.download_text_data(limit=arxiv_limit)
            total += self.download_sequence_data(limit=seq_limit)
            total += self.download_structure_data()
            total += self.download_image_data(limit=image_limit)
            
            self._log("\n" + "="*70)
            self._log(f"✅ Download Complete! Total items: {total}")
            self._log(f"📁 Data saved to: {self.data_dir}")
            self._log("="*70)
            return total
            
        except Exception as e:
            self._log(f"\n❌ Download failed: {e}")
            return total


def main():
    parser = argparse.ArgumentParser(
        description="Automated data downloader for QDesign pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_data.py --all                    # Download everything
  python download_data.py --text --limit 20        # Download 20 arXiv papers
  python download_data.py --sequence --limit 100   # Download 100 sequences
  python download_data.py --structure              # Download all structures
  python download_data.py --image --limit 15       # Download 15 images
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Download all data types')
    parser.add_argument('--text', action='store_true', help='Download text/papers')
    parser.add_argument('--sequence', action='store_true', help='Download protein sequences')
    parser.add_argument('--structure', action='store_true', help='Download protein structures')
    parser.add_argument('--image', action='store_true', help='Download images')
    parser.add_argument('--limit', type=int, default=20, help='Number of items to download (default: 20)')
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
            downloader.download_all(arxiv_limit=args.limit, seq_limit=args.limit, image_limit=args.limit)
        else:
            if args.text:
                downloader.download_text_data(args.query, args.limit)
            if args.sequence:
                downloader.download_sequence_data(args.limit)
            if args.structure:
                downloader.download_structure_data()
            if args.image:
                downloader.download_image_data(args.limit)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()