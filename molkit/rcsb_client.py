"""
RCSB PDB API client.
Uses only stdlib (urllib) — no external dependencies.
"""

import json
import urllib.request
import urllib.error
from typing import Optional


SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
GRAPHQL_URL = "https://data.rcsb.org/graphql"


def _post_json(url: str, payload: dict, timeout: float = 10.0) -> dict:
    """POST JSON and return parsed response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_pdb(query: str, max_results: int = 10) -> list[str]:
    """
    Full-text search on RCSB. Returns list of PDB IDs.
    """
    payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": query},
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": max_results},
            "results_content_type": ["experimental"],
        },
    }
    try:
        result = _post_json(SEARCH_URL, payload)
        return [r["identifier"] for r in result.get("result_set", [])]
    except Exception:
        return []


# GraphQL query that fetches everything we need for the inspector
_ENTRY_QUERY = """
query($id: String!) {
  entry(entry_id: $id) {
    rcsb_id
    struct { title }
    exptl { method }
    rcsb_entry_info {
      resolution_combined
      molecular_weight
      deposited_atom_count
      polymer_entity_count
      nonpolymer_entity_count
      polymer_composition
    }
    rcsb_accession_info { deposit_date initial_release_date }
    rcsb_primary_citation {
      title journal_abbrev year
      pdbx_database_id_PubMed pdbx_database_id_DOI
      rcsb_authors
    }
    citation {
      id title journal_abbrev year
      pdbx_database_id_PubMed pdbx_database_id_DOI
      rcsb_authors
    }
    polymer_entities {
      rcsb_id
      rcsb_polymer_entity { pdbx_description formula_weight }
      entity_poly {
        pdbx_seq_one_letter_code_can type rcsb_entity_polymer_type
      }
      rcsb_entity_source_organism { ncbi_scientific_name }
      rcsb_polymer_entity_annotation {
        annotation_id type
        annotation_lineage { id name }
      }
      rcsb_polymer_entity_feature {
        type name
        feature_positions { beg_seq_id end_seq_id }
      }
      polymer_entity_instances {
        rcsb_id
        rcsb_polymer_instance_annotation {
          annotation_id type
          annotation_lineage { id name }
        }
        rcsb_polymer_instance_feature {
          type name
          feature_positions { beg_seq_id end_seq_id }
        }
      }
    }
    nonpolymer_entities {
      rcsb_nonpolymer_entity { pdbx_description formula_weight }
      nonpolymer_comp {
        chem_comp { name type formula }
      }
    }
  }
}
"""

# Lighter query for search result cards (batch)
_BATCH_QUERY = """
query($ids: [String!]!) {
  entries(entry_ids: $ids) {
    rcsb_id
    struct { title }
    exptl { method }
    rcsb_entry_info { resolution_combined molecular_weight }
    rcsb_accession_info { deposit_date }
    polymer_entities {
      rcsb_polymer_entity { pdbx_description }
      rcsb_entity_source_organism { ncbi_scientific_name }
    }
  }
}
"""


def fetch_entry_metadata(pdb_id: str) -> Optional[dict]:
    """Fetch full metadata for a single PDB entry. Returns raw GraphQL data."""
    try:
        result = _post_json(GRAPHQL_URL, {
            "query": _ENTRY_QUERY,
            "variables": {"id": pdb_id.upper()},
        })
        return result.get("data", {}).get("entry")
    except Exception:
        return None


def fetch_batch_metadata(pdb_ids: list[str]) -> list[dict]:
    """Fetch summary metadata for multiple PDB entries."""
    if not pdb_ids:
        return []
    try:
        result = _post_json(GRAPHQL_URL, {
            "query": _BATCH_QUERY,
            "variables": {"ids": [pid.upper() for pid in pdb_ids]},
        })
        return result.get("data", {}).get("entries") or []
    except Exception:
        return []


def parse_entry_summary(entry: dict) -> dict:
    """Parse a GraphQL entry into a flat summary dict for display."""
    if not entry:
        return {}

    info = entry.get("rcsb_entry_info") or {}
    exptl = (entry.get("exptl") or [{}])[0]
    acc = entry.get("rcsb_accession_info") or {}

    # Find primary organism
    organism = ""
    for pe in entry.get("polymer_entities") or []:
        for org in pe.get("rcsb_entity_source_organism") or []:
            name = org.get("ncbi_scientific_name", "")
            if name:
                organism = name
                break
        if organism:
            break

    res = info.get("resolution_combined")
    resolution = res[0] if res else None

    return {
        "pdb_id": entry.get("rcsb_id", ""),
        "title": (entry.get("struct") or {}).get("title", ""),
        "method": exptl.get("method", ""),
        "resolution": resolution,
        "molecular_weight": info.get("molecular_weight"),
        "atom_count": info.get("deposited_atom_count"),
        "polymer_count": info.get("polymer_entity_count"),
        "organism": organism,
        "deposit_date": (acc.get("deposit_date") or "")[:10],
    }
