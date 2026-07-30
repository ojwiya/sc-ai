# Overseas Property RAG MVP — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> Each task is self-contained and can be executed by a leaf subagent with zero prior context.

**Goal:** Turn the scraped 11,960-property dataset into a working RAG demo — build vector store, CLI search tool, and verification harness, then push to GitHub.

**Architecture:** ChromaDB vector store (all-MiniLM-L6-v2 embeddings) + CLI search script. Properties are embedded as text chunks; queries return top-N matches with metadata. A separate verification harness validates the pipeline end-to-end.

**Tech Stack:** Python 3.14, chromadb 1.5.9, json, argparse. No web framework — CLI only for the MVP.

**Current state:** 
- `properties_data.json` — 11,960 raw properties (31 MB)
- `properties_clean.json` — normalized version with country names, price brackets, property types
- `scrape.py` — working API scraper
- `normalize_data.py` — working data normalizer
- `rag_pipeline.py` — coded but chromadb import fails in Hermes subprocess (works in main terminal)
- `.gitignore` — excludes large data files
- README.md — basic

**Remaining gaps:**
- chromadb works in the main terminal (`python3 -c "import chromadb"` succeeds at /usr/local/bin/python3) but background/hermes subprocess uses different interpreter
- Missing countries: Ireland, Australia, New Zealand, Dubai (not present in 600 pages of "recently added" sort)
- Git remote not pushed (SSH blocked, repo not created on GitHub)
- No end-to-end verification harness

---

## Phase 1: Fix & Build Vector Store (tasks 1-4)

### Task 1: Verify ChromaDB availability and pin Python interpreter

**Objective:** Confirm chromadb is importable from the Python that will be used, and record the exact path.

**Files:**
- Create: `scripts/check_env.py`

**Step 1: Create environment check script**

Create file `scripts/check_env.py`:
```python
#!/usr/bin/env python3
"""Verify all dependencies are available."""
import sys, json

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

deps = {
    'chromadb': 'chromadb',
    'json': 'json',
    're': 're',
    'argparse': 'argparse',
}

results = {}
for name, module in deps.items():
    try:
        __import__(module)
        results[name] = 'OK'
        if name == 'chromadb':
            import chromadb
            print(f"chromadb version: {chromadb.__version__}")
    except ImportError as e:
        results[name] = f'MISSING: {e}'

print(json.dumps(results, indent=2))
all_ok = all(v == 'OK' for v in results.values())
print(f"\nOVERALL: {'READY' if all_ok else 'NOT READY'}")
sys.exit(0 if all_ok else 1)
```

**Step 2: Run the check**

```bash
cd /Users/admin/Documents/sc-ai && python3 scripts/check_env.py
```

Expected output: All `OK`, chromadb version printed, `OVERALL: READY`, exit code 0.

**Step 3: If chromadb is MISSING, install it**

```bash
python3 -m pip install chromadb
```

Then re-run Step 2.

**Step 4: Commit**

```bash
git add scripts/check_env.py
git commit -m "chore: add environment check script"
```

**Note to implementer:** If chromadb consistently fails in the subprocess but works in the main terminal, create a wrapper shell script at `scripts/build_vector_store.sh` that explicitly uses `/usr/local/bin/python3` and run the next tasks via that script.

---

### Task 2: Create the index builder script

**Objective:** Build a standalone script that reads `properties_data.json`, embeds all properties into ChromaDB, and saves the vector store to `chroma_db/`.

**Files:**
- Create: `scripts/build_index.py`

**Step 1: Create the script**

Create file `scripts/build_index.py`:
```python
#!/usr/bin/env python3
"""
Build ChromaDB vector store from scraped property data.
Run once to create the index, then use search_properties.py to query.

Usage: python3 scripts/build_index.py [--batch-size 200] [--data-file properties_data.json]
"""
import json, os, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / 'properties_data.json'
DEFAULT_CHROMA = ROOT / 'chroma_db'

def format_property_text(p):
    """Format a property into a searchable text chunk for embeddings."""
    currency_map = {"EUR": "€", "GBP": "£", "USD": "$", "CHF": "CHF"}
    curr = currency_map.get(p.get('currencyCode', 'EUR'), p.get('currencyCode', '€'))
    
    parts = [
        p.get('title', 'Untitled'),
        f"Located in {p.get('locationName', 'Unknown')}, {p.get('country_slug', 'Unknown')}",
        f"Price: {curr}{p.get('price', 0):,.0f}",
    ]
    if p.get('bedrooms'):
        parts.append(f"{p['bedrooms']} bedroom{'s' if p['bedrooms'] != 1 else ''}")
    if p.get('bathrooms'):
        parts.append(f"{p['bathrooms']} bathroom{'s' if p['bathrooms'] != 1 else ''}")
    if p.get('buildSize'):
        parts.append(f"Build size: {p['buildSize']} square meters")
    if p.get('plotSize'):
        parts.append(f"Plot size: {p['plotSize']} square meters")
    if p.get('description'):
        parts.append(p['description'][:600])
    
    return ' | '.join(parts)


def main():
    parser = argparse.ArgumentParser(description='Build ChromaDB property index')
    parser.add_argument('--batch-size', type=int, default=200, help='Batch size for embedding')
    parser.add_argument('--data-file', default=str(DEFAULT_DATA), help='Path to properties_data.json')
    parser.add_argument('--chroma-dir', default=str(DEFAULT_CHROMA), help='Path to ChromaDB directory')
    parser.add_argument('--collection', default='overseas_properties', help='Collection name')
    args = parser.parse_args()
    
    # Load data
    print(f"Loading {args.data_file}...")
    with open(args.data_file) as f:
        data = json.load(f)
    properties = data['properties']
    print(f"Loaded {len(properties)} properties from {len(data['country_distribution'])} countries")
    
    # Import chromadb (lazy so check_env catches import issues first)
    import chromadb
    
    # Create client and collection
    client = chromadb.PersistentClient(path=args.chroma_dir)
    try:
        client.delete_collection(args.collection)
        print(f"Deleted existing collection '{args.collection}'")
    except:
        pass
    
    collection = client.create_collection(
        name=args.collection,
        metadata={"description": "Your Overseas Home property listings"}
    )
    
    # Batch insert
    total = len(properties)
    for i in range(0, total, args.batch_size):
        batch = properties[i:i + args.batch_size]
        ids = [str(p['id']) for p in batch]
        documents = [format_property_text(p) for p in batch]
        metadatas = [{
            'title': p.get('title', ''),
            'country': p.get('country_slug', ''),
            'location': p.get('locationName', ''),
            'price': float(p['price']),
            'currency': p.get('currencyCode', 'EUR'),
            'bedrooms': int(p.get('bedrooms') or 0),
            'bathrooms': int(p.get('bathrooms') or 0),
            'buildSize': p.get('buildSize') or 0,
            'plotSize': p.get('plotSize') or 0,
        } for p in batch]
        
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        
        done = min(i + args.batch_size, total)
        if done % 1000 == 0 or done == total:
            print(f"  Embedded {done}/{total} ({done*100//total}%)")
    
    print(f"\nDone. Collection '{args.collection}' has {collection.count()} documents.")
    print(f"Vector store saved to: {args.chroma_dir}")
    
    # Quick verification
    results = collection.query(query_texts=["villa in Spain with pool"], n_results=3)
    print(f"\nQuick verification query: 'villa in Spain with pool'")
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"  {i+1}. {meta['title']} — {meta['location']} — {meta['currency']}{meta['price']:,.0f}")


if __name__ == '__main__':
    main()
```

**Step 2: Test with a small subset first**

```bash
cd /Users/admin/Documents/sc-ai

# Create a tiny test dataset
python3 -c "
import json
d = json.load(open('properties_data.json'))
d['properties'] = d['properties'][:100]
json.dump(d, open('test_data.json', 'w'))
print('Created test_data.json with 100 properties')
"

# Build index with test data
python3 scripts/build_index.py --data-file test_data.json --chroma-dir test_chroma_db --batch-size 20
```

Expected: Embeds 100 properties, prints verification query results.

**Step 3: Clean up test artifacts**

```bash
rm test_data.json
rm -rf test_chroma_db
```

**Step 4: Build the full index**

```bash
python3 scripts/build_index.py
```

Expected: Embeds 11,960 properties (takes ~2-3 minutes), prints final count and verification results.

**Step 5: Commit**

```bash
git add scripts/build_index.py
git commit -m "feat: add ChromaDB index builder script"
```

---

### Task 3: Create the search CLI script

**Objective:** Build a command-line search tool that queries the ChromaDB vector store and returns formatted results.

**Files:**
- Create: `scripts/search.py`

**Step 1: Create the script**

Create file `scripts/search.py`:
```python
#!/usr/bin/env python3
"""
Search overseas properties using natural language queries against ChromaDB.

Usage:
  python3 scripts/search.py "3 bedroom villa in Spain under 500k"
  python3 scripts/search.py --country france "farmhouse with land"
  python3 scripts/search.py --max-price 300000 "apartment in Portugal near beach"
  python3 scripts/search.py --list-countries
"""

import argparse, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = ROOT / 'chroma_db'
COLLECTION_NAME = 'overseas_properties'

CURRENCY_SYMBOL = {'EUR': '€', 'GBP': '£', 'USD': '$', 'CHF': 'CHF'}


def search(query, n=5, country=None, max_price=None, min_beds=None):
    """Search properties and return formatted results."""
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    
    # Build filter if needed
    where = {}
    if country:
        where['country'] = country
    if max_price is not None:
        where['price'] = {'$lte': float(max_price)}
    if min_beds is not None:
        where['bedrooms'] = {'$gte': int(min_beds)}
    
    kwargs = {'query_texts': [query], 'n_results': n}
    if where:
        kwargs['where'] = where
    
    results = collection.query(**kwargs)
    return results


def format_results(results):
    """Pretty-print search results."""
    output = []
    for i in range(len(results['ids'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        similarity = 1.0 - dist
        
        curr = CURRENCY_SYMBOL.get(meta.get('currency', 'EUR'), meta.get('currency', ''))
        
        output.append(f"\n{'─'*60}")
        output.append(f"#{i+1}  {meta.get('title', 'Unknown')}")
        output.append(f"     {meta.get('location', 'Unknown')} | {meta.get('country', 'Unknown').title()}")
        output.append(f"     Price: {curr}{meta.get('price', 0):,.0f} | "
                      f"Beds: {meta.get('bedrooms', '?')} | "
                      f"Baths: {meta.get('bathrooms', '?')} | "
                      f"Similarity: {similarity:.3f}")
        if meta.get('buildSize'):
            output.append(f"     Build: {meta['buildSize']} m²")
        if meta.get('plotSize'):
            output.append(f"     Plot: {meta['plotSize']} m²")
        # Preview first 2 lines of the document
        doc_lines = doc.split('|')[:3]
        output.append(f"     {doc_lines[0].strip()[:100]}")
    
    return '\n'.join(output)


def list_countries():
    """List available countries in the collection."""
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    
    # Get all metadata and count by country
    results = collection.get(include=['metadatas'])
    from collections import Counter
    countries = Counter(m['country'] for m in results['metadatas'])
    
    print(f"\nCountries in index ({collection.count()} total properties):")
    for country, count in countries.most_common():
        print(f"  {country:20s} {count:>6,d}")


def main():
    parser = argparse.ArgumentParser(description='Search overseas properties with RAG')
    parser.add_argument('query', nargs='?', help='Natural language search query')
    parser.add_argument('--country', '-c', help='Filter by country slug (e.g. spain, france)')
    parser.add_argument('--max-price', '-p', type=float, help='Maximum price')
    parser.add_argument('--min-beds', '-b', type=int, help='Minimum bedrooms')
    parser.add_argument('--results', '-n', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--list-countries', action='store_true', help='List available countries')
    args = parser.parse_args()
    
    # Check if index exists
    if not (CHROMA_DIR / 'chroma.sqlite3').exists():
        print("ERROR: Vector store not found. Run 'python3 scripts/build_index.py' first.")
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
        n=args.results,
        country=args.country,
        max_price=args.max_price,
        min_beds=args.min_beds
    )
    
    print(f"\nSearch: \"{args.query}\"")
    if args.country:
        print(f"Filter: country={args.country}")
    if args.max_price:
        print(f"Filter: max price={args.max_price}")
    if args.min_beds:
        print(f"Filter: min beds={args.min_beds}")
    
    print(format_results(results))
    print()


if __name__ == '__main__':
    main()
```

**Step 2: Test the search CLI**

```bash
cd /Users/admin/Documents/sc-ai

# Test listing countries
python3 scripts/search.py --list-countries

# Test basic search
python3 scripts/search.py "3 bedroom villa in Spain near the beach"

# Test with country filter
python3 scripts/search.py --country portugal "apartment with sea views"

# Test with price filter
python3 scripts/search.py --max-price 200000 "cheap house in France"

# Test with bedroom filter
python3 scripts/search.py --min-beds 4 "large family home in Italy"
```

Expected: Each query returns 5 formatted results with title, location, price, similarity score.

**Step 3: Commit**

```bash
git add scripts/search.py
git commit -m "feat: add CLI search tool with filters"
```

---

### Task 4: Create the verification harness

**Objective:** Build a script that runs a set of known queries and validates results are returned correctly.

**Files:**
- Create: `tests/test_search.py`

**Step 1: Create the test script**

Create file `tests/test_search.py`:
```python
#!/usr/bin/env python3
"""
Verification harness for the RAG pipeline.
Runs a set of queries and validates:
1. Results are returned for every query
2. Country filters work correctly
3. Price filters work correctly
4. Bedroom filters work correctly
"""

import sys, os, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

from search import search, CHROMA_DIR, COLLECTION_NAME

PASS = 0
FAIL = 0


def check(name, condition, detail=''):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} — {detail}")


def run_tests():
    global PASS, FAIL
    PASS = 0
    FAIL = 0
    
    print("=" * 60)
    print("RAG Pipeline Verification Harness")
    print("=" * 60)
    
    # Test 1: Index exists
    print("\n[Test 1] Vector store exists")
    index_file = CHROMA_DIR / 'chroma.sqlite3'
    check("chroma.sqlite3 found", index_file.exists(), str(index_file))
    
    # Test 2: Basic query returns results
    print("\n[Test 2] Basic queries return results")
    queries = [
        "villa in Spain with pool",
        "cheap apartment in France",
        "house in Portugal near the beach",
        "ski property in the Alps",
        "luxury home in Cyprus",
        "farmhouse in Italy",
        "modern apartment in Malta",
    ]
    for q in queries:
        try:
            results = search(q, n=3)
            has_results = len(results['ids'][0]) > 0
            check(f"Query: '{q}'", has_results, f"got {len(results['ids'][0])} results")
        except Exception as e:
            check(f"Query: '{q}'", False, str(e))
    
    # Test 3: Country filter works
    print("\n[Test 3] Country filter")
    countries = ['spain', 'france', 'portugal', 'italy', 'cyprus']
    for c in countries:
        try:
            results = search("property", n=3, country=c)
            all_match = all(m['country'] == c for m in results['metadatas'][0])
            check(f"Country filter '{c}'", all_match and len(results['ids'][0]) > 0,
                  f"{len(results['ids'][0])} results, all {c}")
        except Exception as e:
            check(f"Country filter '{c}'", False, str(e))
    
    # Test 4: Price filter works
    print("\n[Test 4] Price filter")
    try:
        results = search("villa", n=5, max_price=200000)
        all_under = all(float(m['price']) <= 200000 for m in results['metadatas'][0])
        check("Max price €200k", all_under and len(results['ids'][0]) > 0,
              f"max={max(m['price'] for m in results['metadatas'][0])}")
    except Exception as e:
        check("Max price €200k", False, str(e))
    
    # Test 5: Bedroom filter works
    print("\n[Test 5] Bedroom filter")
    try:
        results = search("property", n=5, min_beds=4)
        all_match = all(int(m['bedrooms']) >= 4 for m in results['metadatas'][0])
        check("Min 4 bedrooms", all_match and len(results['ids'][0]) > 0,
              f"beds={[m['bedrooms'] for m in results['metadatas'][0]]}")
    except Exception as e:
        check("Min 4 bedrooms", False, str(e))
    
    # Test 6: Combined filters
    print("\n[Test 6] Combined filters")
    try:
        results = search("villa", n=5, country='spain', max_price=500000, min_beds=3)
        all_spain = all(m['country'] == 'spain' for m in results['metadatas'][0])
        all_under = all(float(m['price']) <= 500000 for m in results['metadatas'][0])
        all_beds = all(int(m['bedrooms']) >= 3 for m in results['metadatas'][0])
        check("Spain + max €500k + 3+ beds", all_spain and all_under and all_beds and len(results['ids'][0]) > 0)
    except Exception as e:
        check("Combined filters", False, str(e))
    
    # Summary
    total = PASS + FAIL
    print(f"\n{'='*60}")
    print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed")
    print(f"{'='*60}")
    
    return FAIL == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
```

**Step 2: Create tests directory and run**

```bash
cd /Users/admin/Documents/sc-ai
mkdir -p tests
python3 tests/test_search.py
```

Expected: All tests pass (or mostly pass; some queries like "cheap apartment in France" might return few results — that's OK for MVP).

**Step 3: Commit**

```bash
git add tests/test_search.py
git commit -m "test: add RAG pipeline verification harness"
```

---

## Phase 2: Demo & Polish (tasks 5-7)

### Task 5: Create end-to-end demo script

**Objective:** A single script that loads data, builds index, runs demo queries, and prints results — all in one command.

**Files:**
- Create: `demo.py`

**Step 1: Create demo script**

Create file `demo.py`:
```python
#!/usr/bin/env python3
"""
End-to-end demo of the overseas property RAG pipeline.
Runs the full pipeline: loads data → builds index → runs queries → shows results.

Usage: python3 demo.py
"""

import subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEMO_QUERIES = [
    ("Beach villa in Spain", "3 bedroom villa in Spain near the beach under 500000 euros"),
    ("French countryside", "cheap countryside house in France with garden and land"),
    ("Portugal apartment", "modern apartment in Portugal with sea views"),
    ("Ski chalet", "ski property in the French Alps for winter holidays"),
    ("Italian farmhouse", "traditional farmhouse in Italy with land"),
    ("Cyprus investment", "affordable apartment in Cyprus for investment"),
    ("Luxury villa", "luxury villa with infinity pool and panoramic views"),
    ("Budget home", "cheapest house under 100000 euros anywhere"),
    ("Family home", "4 bedroom family house with garden near good schools"),
]


def run_step(name, cmd):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(ROOT))
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        print(f"  ✗ FAILED (exit code {result.returncode})")
    return result.returncode == 0


def main():
    print("=" * 60)
    print("  Overseas Property RAG — End-to-End Demo")
    print("=" * 60)
    
    # Step 1: Check environment
    if not run_step("1/4 Checking environment", "python3 scripts/check_env.py"):
        print("\nEnvironment not ready. Run: pip3 install chromadb")
        return False
    
    # Step 2: Build index (or verify exists)
    index_file = ROOT / 'chroma_db' / 'chroma.sqlite3'
    if index_file.exists():
        print(f"\n  Index already exists at {index_file}")
    else:
        if not run_step("2/4 Building vector index", "python3 scripts/build_index.py"):
            return False
    
    # Step 3: Run demo queries
    print(f"\n{'='*60}")
    print(f"  3/4 Running demo queries")
    print(f"{'='*60}")
    
    from scripts.search import search, format_results
    
    for name, query in DEMO_QUERIES:
        print(f"\n{'─'*60}")
        print(f"  🏠 {name}")
        print(f"  🔍 \"{query}\"")
        try:
            results = search(query, n=3)
            print(format_results(results))
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Step 4: Summary
    print(f"\n{'='*60}")
    print(f"  Demo complete!")
    print(f"  Index: {ROOT / 'chroma_db'}")
    print(f"  Search CLI: python3 scripts/search.py \"<query>\"")
    print(f"  Tests:     python3 tests/test_search.py")
    print(f"{'='*60}")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
```

**Step 2: Test the demo**

```bash
cd /Users/admin/Documents/sc-ai
python3 demo.py
```

Expected: Runs through all 4 steps, prints formatted search results for each query.

**Step 3: Commit**

```bash
git add demo.py
git commit -m "feat: add end-to-end demo script"
```

---

### Task 6: Update README with complete documentation

**Objective:** Replace the basic README with a comprehensive one covering setup, usage, and architecture.

**Files:**
- Modify: `README.md`

**Step 1: Replace README content**

Replace the entire contents of `README.md` with:

```markdown
# rag-property-search-poc — Overseas Property RAG

RAG (Retrieval-Augmented Generation) pipeline for searching 11,960 overseas properties scraped from [Your Overseas Home](https://www.youroverseashome.com/).

## Quick Start

```bash
# 1. Install dependencies
pip3 install chromadb

# 2. Verify environment
python3 scripts/check_env.py

# 3. Build the vector index (~2-3 min)
python3 scripts/build_index.py

# 4. Search!
python3 scripts/search.py "3 bedroom villa in Spain near the beach"
```

## Dataset

11,960 properties across 9 countries:

| Country      | Count  |
|-------------|--------|
| Spain       | 7,787  |
| Cyprus      | 1,478  |
| Portugal    | 1,060  |
| France      | 692    |
| Italy       | 558    |
| USA         | 184    |
| Malta       | 76     |
| Switzerland | 70     |
| Greece      | 55     |

**Property types:** Houses (4,939), Apartments (4,340), Villas (2,218), Land (355), Other (108)

**Price brackets:** Mid-range €250k-500k (4,838), Premium (2,678), Affordable (2,446), Luxury (1,674), Budget (324)

## Project Structure

```
rag-property-search-poc/
├── demo.py                 # End-to-end demo
├── scrape.py               # API scraper (11,960 properties)
├── normalize_data.py       # Data enrichment (country names, types, brackets)
├── rag_pipeline.py         # Original RAG script (reference)
├── scripts/
│   ├── build_index.py      # ChromaDB index builder
│   ├── search.py           # CLI search tool
│   └── check_env.py        # Environment verification
├── tests/
│   └── test_search.py      # Verification harness
├── properties_data.json    # Raw scraped data (not in git)
├── properties_clean.json   # Normalized data (not in git)
├── chroma_db/              # Vector store (not in git)
└── README.md
```

## Search Examples

```bash
# Basic search
python3 scripts/search.py "villa with pool near the beach"

# Filter by country
python3 scripts/search.py --country france "farmhouse with garden"

# Filter by price
python3 scripts/search.py --max-price 200000 "cheap apartment"

# Filter by bedrooms
python3 scripts/search.py --min-beds 4 "large family home"

# Combined filters
python3 scripts/search.py --country spain --max-price 500000 --min-beds 3 "villa near golf"

# List available countries
python3 scripts/search.py --list-countries
```

## Architecture

- **Data source:** Your Overseas Home REST API (`property-portal-api-gw.youroverseashome.com`)
- **Scraper:** Python + urllib, 4 properties per API call, 3,000 pages
- **Vector store:** ChromaDB with all-MiniLM-L6-v2 embeddings
- **Embedding model:** sentence-transformers/all-MiniLM-L6-v2 (auto-downloaded by ChromaDB)
- **Search:** Cosine similarity with optional metadata filters (country, price, bedrooms)

## API Details

```
POST https://property-portal-api-gw.youroverseashome.com/api/v1/properties/search
Body: {"page": 1, "size": 4}
Returns: {statusCode, data: {totalCount: 128311, properties: [...]}}
```

## License

Data scraped from Your Overseas Home for research/demo purposes.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: comprehensive README with setup, usage, architecture"
```

---

### Task 7: Add convenience Makefile

**Objective:** Add a Makefile so all operations can be run with simple `make` commands.

**Files:**
- Create: `Makefile`

**Step 1: Create Makefile**

Create file `Makefile`:
```makefile
.PHONY: help install check build search test demo clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip3 install chromadb

check: ## Verify environment is ready
	python3 scripts/check_env.py

build: ## Build the ChromaDB vector index
	python3 scripts/build_index.py

search: ## Run an example search (pass QUERY= env var)
	python3 scripts/search.py "$(QUERY)"

test: ## Run verification tests
	python3 tests/test_search.py

demo: ## Run the end-to-end demo
	python3 demo.py

clean: ## Remove vector store
	rm -rf chroma_db/
```

**Step 2: Test each make target**

```bash
cd /Users/admin/Documents/sc-ai
make help
make check
make test
make search QUERY="villa in Spain"
```

**Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: add Makefile for convenience commands"
```

---

## Phase 3: Git Push (task 8)

### Task 8: Push to GitHub

**Objective:** Push the repo to GitHub.

**Background:** SSH to GitHub (port 22) is blocked by firewall. The repo `rag-property-search-poc` does not yet exist on GitHub under the `ojwiya` account.

**Step 1: Create the repo on GitHub**

The user needs to create `rag-property-search-poc` repository on GitHub (either manually at github.com/new or via `gh repo create`).

**Step 2: Set up HTTPS remote with token**

```bash
cd /Users/admin/Documents/sc-ai

# Remove the SSH remote
git remote remove origin

# Add HTTPS remote (user needs to replace TOKEN with their personal access token)
git remote add origin https://TOKEN@github.com/ojwiya/rag-property-search-poc.git

# Push
git push -u origin main
```

**Alternative if `gh` CLI is available:**

```bash
gh auth login
gh repo create ojwiya/rag-property-search-poc --public --source=. --remote=origin --push
```

**Step 3: Verify**

```bash
git remote -v
# Should show: origin  https://github.com/ojwiya/rag-property-search-poc.git
```

---

## Task Dependency Graph

```
Task 1 (check_env) ──┐
                      ├──> Task 2 (build_index) ──> Task 4 (test harness)
                      │               │
                      │               └──> Task 3 (search CLI)
                      │                              │
                      └──────────────────────────────┴──> Task 5 (demo)
                                                                 │
                                                                 └──> Task 6 (README) + Task 7 (Makefile)
                                                                              │
                                                                              └──> Task 8 (Git push)
```

- **Parallelizable:** Tasks 2 & 3 can run in parallel after Task 1
- **Sequential:** Tasks 5, 6, 7, 8 depend on all prior tasks
- **Task 8 requires user action:** GitHub repo creation and token/SSH setup

---

## Quick-Start for a Subagent

Each subagent implementing these tasks needs this context block pasted into its `context` field:

```
PROJECT: Overseas property RAG pipeline (rag-property-search-poc)
ROOT: /Users/admin/Documents/sc-ai
PYTHON: /usr/local/bin/python3 (use `python3` in commands)
CHROMADB: 1.5.9, installed and importable
DATA: properties_data.json (11,960 properties, 9 countries, 31 MB)

KEY FILES:
- scripts/check_env.py — verify deps
- scripts/build_index.py — build ChromaDB vector store
- scripts/search.py — CLI search tool
- tests/test_search.py — verification harness
- demo.py — end-to-end demo
- Makefile — convenience commands
- scrape.py — data scraper (already working)
- normalize_data.py — data normalizer (already working)
- properties_data.json — raw data (31 MB, gitignored)
- properties_clean.json — normalized data (gitignored)
- chroma_db/ — vector store directory (gitignored)

IMPORTANT: Always run commands with `cd /Users/admin/Documents/sc-ai &&` prefix.
```