import re
import sys
from pathlib import Path

import httpx


ARXIV_API = "https://export.arxiv.org/api/query"
BIO_QUERY = "cat:q-bio.* OR cat:bio.*"


def fetch_bio_papers(limit: int, out_dir: Path) -> None:
    params = {"search_query": BIO_QUERY, "start": 0, "max_results": limit}
    response = httpx.get(ARXIV_API, params=params, timeout=30, follow_redirects=True)
    response.raise_for_status()
    ids = re.findall(r"<id>http://arxiv.org/abs/([^<]+)</id>", response.text)
    out_dir.mkdir(parents=True, exist_ok=True)
    for arxiv_id in ids[:limit]:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_resp = httpx.get(pdf_url, timeout=60, follow_redirects=True)
        pdf_resp.raise_for_status()
        (out_dir / f"{arxiv_id}.pdf").write_bytes(pdf_resp.content)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fetch_bio_arxiv_papers.py <limit>")
        return 1
    fetch_bio_papers(int(sys.argv[1]), Path("data/pdf"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
