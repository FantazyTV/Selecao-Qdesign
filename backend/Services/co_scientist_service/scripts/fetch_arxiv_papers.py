import re
import sys
from pathlib import Path

import httpx


ARXIV_API = "https://export.arxiv.org/api/query"


def fetch_papers(query: str, limit: int, out_dir: Path) -> None:
    params = {"search_query": query, "start": 0, "max_results": limit}
    response = httpx.get(ARXIV_API, params=params, timeout=30, follow_redirects=True)
    response.raise_for_status()
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = re.findall(r"<id>http://arxiv.org/abs/([^<]+)</id>", response.text)
    for arxiv_id in ids[:limit]:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_resp = httpx.get(pdf_url, timeout=60)
        pdf_resp.raise_for_status()
        (out_dir / f"{arxiv_id}.pdf").write_bytes(pdf_resp.content)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: fetch_arxiv_papers.py <query> <limit>")
        return 1
    fetch_papers(sys.argv[1], int(sys.argv[2]), Path("data/pdf"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
