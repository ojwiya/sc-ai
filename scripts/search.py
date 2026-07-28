#!/usr/bin/env python3
"""
Search overseas properties using natural language queries against ChromaDB.

Usage:
  python3 scripts/search.py "3 bedroom villa in Spain under 500k"
  python3 scripts/search.py --country spain --max-price 500000 --bedrooms 3 "villa with pool"
  python3 scripts/search.py --json "apartment in Portugal" > results.json
  python3 scripts/search.py --list-countries
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = ROOT / 'chroma_db'
COLLECTION_NAME = 'overseas_properties'

CURRENCY_SYMBOL = {'EUR': '€', 'GBP': '£', 'USD': '$', 'CHF': 'CHF'}


def search(query, limit=10, country=None, max_price=None, min_price=None,
           min_bedrooms=None):
    """Search properties and return a list of result dicts."""
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    where = {}
    if country:
        where['country'] = country
    if min_price is not None:
        where.setdefault('price', {})['$gte'] = float(min_price)
    if max_price is not None:
        where.setdefault('price', {})['$lte'] = float(max_price)
    if min_bedrooms is not None:
        where['bedrooms'] = {'$gte': int(min_bedrooms)}

    kwargs = {'query_texts': [query], 'n_results': limit}
    if where:
        kwargs['where'] = where

    results = collection.query(**kwargs)

    output = []
    for i in range(len(results['ids'][0])):
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        output.append({
            'title': meta.get('title', 'Unknown'),
            'price': meta.get('price', 0),
            'currency': meta.get('currency', 'EUR'),
            'location': meta.get('location', 'Unknown'),
            'country': meta.get('country', 'Unknown'),
            'bedrooms': meta.get('bedrooms', 0),
            'bathrooms': meta.get('bathrooms', 0),
            'score': round(1.0 - dist, 4),
        })
    return output


def format_table(results):
    """Format results as a human-readable table."""
    try:
        from tabulate import tabulate
    except ImportError:
        return _format_simple(results)

    rows = []
    for r in results:
        curr = CURRENCY_SYMBOL.get(r['currency'], r['currency'])
        rows.append([
            r['title'][:60],
            r['location'],
            f"{curr}{r['price']:,.0f}",
            r['bedrooms'],
            r['bathrooms'],
            f"{r['score']:.3f}",
        ])

    headers = ['Title', 'Location', 'Price', 'Beds', 'Baths', 'Score']
    return tabulate(rows, headers=headers, tablefmt='simple')


def _format_simple(results):
    """Fallback table format without tabulate."""
    lines = []
    for i, r in enumerate(results):
        curr = CURRENCY_SYMBOL.get(r['currency'], r['currency'])
        lines.append(
            f"{i+1}. {r['title'][:60]} | {r['location']} | {curr}{r['price']:,.0f} | "
            f"{r['bedrooms']}bd {r['bathrooms']}ba | score={r['score']:.3f}"
        )
    return '\n'.join(lines)


def list_countries():
    """List available countries in the collection."""
    import chromadb
    from collections import Counter
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.get(include=['metadatas'])
    countries = Counter(m['country'] for m in results['metadatas'])
    for country, count in countries.most_common():
        print(f"  {country:20s} {count:>6,d}")


def main():
    parser = argparse.ArgumentParser(description='Search overseas properties with RAG')
    parser.add_argument('query', nargs='?', help='Natural language search query')
    parser.add_argument('--country', '-c', help='Filter by country slug (e.g. spain, france)')
    parser.add_argument('--min-price', type=float, help='Minimum price')
    parser.add_argument('--max-price', '-p', type=float, help='Maximum price')
    parser.add_argument('--bedrooms', '-b', type=int, help='Minimum bedrooms')
    parser.add_argument('--limit', '-n', type=int, default=10, help='Number of results (default: 10)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--list-countries', action='store_true', help='List available countries')
    args = parser.parse_args()

    if not (CHROMA_DIR / 'chroma.sqlite3').exists():
        print("ERROR: Vector store not found. Run 'python3 scripts/build_index.py' first.",
              file=sys.stderr)
        sys.exit(1)

    if args.list_countries:
        list_countries()
        return

    if not args.query:
        parser.print_help()
        print("\nExample: python3 scripts/search.py 'villa in Spain with pool'")
        sys.exit(1)

    results = search(
        args.query,
        limit=args.limit,
        country=args.country,
        max_price=args.max_price,
        min_price=args.min_price,
        min_bedrooms=args.bedrooms,
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\nSearch: \"{args.query}\"")
        filters = []
        if args.country:
            filters.append(f"country={args.country}")
        if args.max_price:
            filters.append(f"max price=€{args.max_price:,.0f}")
        if args.min_price:
            filters.append(f"min price=€{args.min_price:,.0f}")
        if args.bedrooms:
            filters.append(f"min bedrooms={args.bedrooms}")
        if filters:
            print(f"Filters: {', '.join(filters)}")
        print(f"Results: {len(results)}\n")
        print(format_table(results))


if __name__ == '__main__':
    main()
