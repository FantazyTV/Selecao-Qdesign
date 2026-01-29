from fastapi import APIRouter, HTTPException, Request
from agent.high_level_tools import protein_graph_from_query
from agent.high_level_tools import protein_graph_from_cif, protein_graph_from_sequence
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ProteinGraphRequest(BaseModel):
    query: Optional[str] = None  # protein name, pdb id, or uniprot id
    cif: Optional[str] = None    # raw CIF text
    sequence: Optional[str] = None  # raw sequence string

@router.post("/protein-graph")
async def build_protein_graph_api(request: ProteinGraphRequest):
    try:
        if request.query:
            graph = protein_graph_from_query.build_protein_graph(request.query)
            return graph
        elif request.cif:
            graph = protein_graph_from_cif.build_protein_graph_from_cif(request.cif)
            return graph
        elif request.sequence:
            graph = protein_graph_from_sequence.build_protein_graph_from_sequence(request.sequence)
            return graph
        else:
            raise HTTPException(status_code=400, detail="No valid input provided. Provide 'query', 'cif', or 'sequence'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
