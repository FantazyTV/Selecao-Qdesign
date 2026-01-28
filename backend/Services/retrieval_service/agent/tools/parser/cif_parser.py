import re
from typing import Dict, Any, List

def parse_cif_file(content: str) -> Dict[str, Any]:
    """
    Parse mmCIF file content to extract key metadata.
    Lightweight parser without heavy dependencies.
    
    Args:
        content: Raw CIF file content as string
        
    Returns:
        Dict with parsed information or error dict
    """
    try:
        lines = content.split('\n')
        parsed = {}
        
        # Extract entry ID
        for line in lines:
            if line.startswith('data_'):
                parsed["entry_id"] = line.replace('data_', '').strip()
                break
        
        if not parsed.get("entry_id"):
            return {"error": "parse_failed", "raw_first_200": content[:200]}
        
        # Extract title
        for line in lines:
            if '_struct.title' in line and len(line.split()) > 1:
                title = ' '.join(line.split()[1:]).strip().strip('"\'')
                parsed["title"] = title
                break
        
        # Extract molecules/entities
        molecules = []
        organisms = []
        chains = []
        
        for line in lines:
            if '_entity.pdbx_description' in line and len(line.split()) > 1:
                desc = ' '.join(line.split()[1:]).strip().strip('"\'')
                molecules.append(desc)
            elif '_entity_src_gen.pdbx_gene_src_scientific_name' in line and len(line.split()) > 1:
                org = ' '.join(line.split()[1:]).strip().strip('"\'')
                organisms.append(org)
            elif '_entity_src_nat.pdbx_organism_scientific' in line and len(line.split()) > 1:
                org = ' '.join(line.split()[1:]).strip().strip('"\'')
                organisms.append(org)
            elif '_struct_asym.id' in line and len(line.split()) > 1:
                chain_id = line.split()[1].strip()
                chains.append(chain_id)
        
        parsed["molecules"] = molecules
        parsed["organisms"] = organisms  
        parsed["chains"] = chains
        
        # Extract coordinate summary (atom count, resolution)
        atom_count = 0
        resolution = None
        
        for line in lines:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                atom_count += 1
            elif '_refine.ls_d_res_high' in line and len(line.split()) > 1:
                try:
                    resolution = float(line.split()[1])
                except ValueError:
                    pass
        
        summary_parts = []
        if atom_count > 0:
            summary_parts.append(f"{atom_count} atoms")
        if resolution:
            summary_parts.append(f"resolution {resolution}Å")
        if chains:
            summary_parts.append(f"{len(chains)} chains")
            
        parsed["summary"] = ", ".join(summary_parts) if summary_parts else "No coordinate data found"

        print(parsed)
        
        return parsed
        
    except Exception as e:
        return {"error": "parse_failed", "raw_first_200": content[:200]}