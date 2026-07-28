#!/usr/bin/env python3
"""End-to-end demo of the overseas property RAG search pipeline."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))

from search import search

DEMO_QUERIES = [
    ("3 bedroom villa in Spain with pool", None),
    ("affordable apartment in Portugal", {"max_price": 200000}),
    ("large family home in Cyprus", {"min_bedrooms": 4}),
]


def main():
    chroma_path = ROOT / 'chroma_db' / 'chroma.sqlite3'
    if not chroma_path.exists():
        print("ERROR: ChromaDB index not found.", file=sys.stderr)
        print("Run: python3 scripts/build_index.py", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("  Overseas Property RAG — Demo")
    print("=" * 60)
    print(f"  Index: {ROOT / 'chroma_db'}")
    print()

    for query, filters in DEMO_QUERIES:
        print(f"Query: \"{query}\"", end="")
        kwargs = {'limit': 5}
        if filters:
            kwargs.update(filters)
            filter_str = ', '.join(f'{k}={v}' for k, v in filters.items())
            print(f"  [{filter_str}]")
        else:
            print()

        results = search(query, **kwargs)
        print(f"  Found: {len(results)} results")
        for i, r in enumerate(results[:5]):
            print(f"  {i+1}. {r['title'][:65]}")
            print(f"     {r['location']} | €{r['price']:,.0f} | "
                  f"{r['bedrooms']}bd {r['bathrooms']}ba | "
                  f"score={r['score']:.3f}")
        print()

    print("=" * 60)
    print("  Demo complete. Try your own queries:")
    print("  python3 scripts/search.py 'your query here'")
    print("=" * 60)


if __name__ == '__main__':
    main()