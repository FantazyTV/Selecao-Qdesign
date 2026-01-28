import requests

def resolve_protein_name(name: str):
    """
    Try to resolve a protein name to a canonical RCSB PDB ID or a UniProt accession.
    - Name (str): the protein name (e.g., "hemoglobin").
    Returns a dict with possible "pdb_ids" and "uniprot_ids".
    """

    resolved = {"pdb_ids": [], "uniprot_ids": []}

    # 1) Try RCSB PDB full-text search
    try:
        pdb_search_url = "https://search.rcsb.org/rcsbsearch/v2/query"
        payload = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": name}
            },
            "return_type": "entry"
        }
        r = requests.post(pdb_search_url, json=payload)
        r.raise_for_status()
        pdb_data = r.json()
        pdb_ids = [item["identifier"] for item in pdb_data.get("result_set", [])]
        resolved["pdb_ids"] = pdb_ids
    except Exception:
        pass

    # 2) Try UniProt text query
    try:
        uniprot_url = "https://rest.uniprot.org/uniprotkb/search"
        params = {"query": name, "format": "json", "fields": "accession"}
        r2 = requests.get(uniprot_url, params=params)
        r2.raise_for_status()
        uq = r2.json()
        uniprot_ids = [item["primaryAccession"] for item in uq.get("results", [])]
        resolved["uniprot_ids"] = uniprot_ids
    except Exception:
        pass

    return resolved