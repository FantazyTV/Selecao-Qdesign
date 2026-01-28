import requests
import os

API_URL = "https://search.rcsb.org/rcsbsearch/v2/query"

# Download a PDB CIF file by ID
def download_pdb_structure(pdb_id, out_dir="pdbs"):
    os.makedirs(out_dir, exist_ok=True)

    pdb_id = pdb_id.upper()

    cif_url = f"https://files.rcsb.org/download/{pdb_id}.cif"
    pdb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"

    cif_path = os.path.join(out_dir, f"{pdb_id}.cif")
    pdb_path = os.path.join(out_dir, f"{pdb_id}.pdb")

    if os.path.exists(cif_path) or os.path.exists(pdb_path):
        print(f"Already exists: {pdb_id}")
        return cif_path if os.path.exists(cif_path) else pdb_path

    r = requests.get(cif_url)
    if r.status_code == 200:
        with open(cif_path, "wb") as f:
            f.write(r.content)
        print(f"Downloaded {pdb_id}.cif")
        return cif_path

    r = requests.get(pdb_url)
    if r.status_code == 200:
        with open(pdb_path, "wb") as f:
            f.write(r.content)
        print(f"Downloaded {pdb_id}.pdb")
        return pdb_path

    print(f"Failed to download {pdb_id} in any format")
    return None

# Download a UniProt FASTA file by ID
def download_uniprot_fasta(uniprot_id, out_dir="fastas"):
    os.makedirs(out_dir, exist_ok=True)
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
    out_file = os.path.join(out_dir, f"{uniprot_id}.fasta")
    if not os.path.exists(out_file):
        try:
            r = requests.get(url)
            r.raise_for_status()
            with open(out_file, "wb") as f:
                f.write(r.content)
            print(f"Downloaded {uniprot_id}")
        except Exception as e:
            print(f"Failed {uniprot_id}: {e}")
    else:
        print(f"Already exists: {uniprot_id}")

if __name__ == "__main__":
    import sys

    pdb_id = sys.argv[1] if len(sys.argv) > 1 else "1EZA"

    print("Testing RCSB download for:", pdb_id)
    path = download_pdb_structure(pdb_id)

    if path:
        print("Saved to:", path)
        print("File size:", os.path.getsize(path), "bytes")
        with open(path, "rb") as f:
            print("First 200 bytes:")
            print(f.read(200))
    else:
        print("Download failed")
