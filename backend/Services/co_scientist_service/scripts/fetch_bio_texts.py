import sys
from pathlib import Path

import httpx


ARXIV_API = "https://export.arxiv.org/api/query"
BIO_QUERY = "cat:q-bio.* OR cat:bio.*"


def fetch_bio_texts(limit: int, out_dir: Path) -> None:
    params = {"search_query": BIO_QUERY, "start": 0, "max_results": limit}
    response = httpx.get(ARXIV_API, params=params, timeout=30, follow_redirects=True)
    response.raise_for_status()
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = response.text.split("<entry>")[1:]
    for idx, entry in enumerate(entries[:limit], start=1):
        title = entry.split("<title>")[1].split("</title>")[0].strip()
        abstract = entry.split("<summary>")[1].split("</summary>")[0].strip()
        content = f"Title: {title}\n\nAbstract:\n{abstract}\n"
        (out_dir / f"arxiv_bio_{idx}.txt").write_text(content, encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fetch_bio_texts.py <limit>")
        return 1
    fetch_bio_texts(int(sys.argv[1]), Path("data/text"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
