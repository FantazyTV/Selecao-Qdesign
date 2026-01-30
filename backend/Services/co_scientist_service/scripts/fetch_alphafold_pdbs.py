import sys
from pathlib import Path

import httpx


def fetch_pdb(uniprot_id: str, out_dir: Path) -> None:
    versions = ["v4", "v3"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for version in versions:
        url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_{version}.pdb"
        response = httpx.get(url, timeout=60, follow_redirects=True)
        if response.status_code == 200:
            (out_dir / f"AF-{uniprot_id}.pdb").write_bytes(response.content)
            return
    if len(uniprot_id) == 4:
        pdb_url = f"https://files.rcsb.org/download/{uniprot_id}.pdb"
        pdb_resp = httpx.get(pdb_url, timeout=60, follow_redirects=True)
        pdb_resp.raise_for_status()
        (out_dir / f"{uniprot_id}.pdb").write_bytes(pdb_resp.content)
        return
    response.raise_for_status()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fetch_alphafold_pdbs.py <UNIPROT_ID> [UNIPROT_ID...] ")
        return 1
    out_dir = Path("data/pdb")
    for uniprot_id in sys.argv[1:]:
        fetch_pdb(uniprot_id, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
