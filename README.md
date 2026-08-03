# RAG  Search for Your Overseas Overseas Home

A RAG (Retrieval-Augmented Generation) pipeline for searching overseas property
listings scraped from [Your Overseas Home](https://www.youroverseashome.com/)
using natural language queries.

See POC website at : [Homes in the Sun](website-rag-search-poc.vercel.app/) 

## What it does

- Scrapes ~11,960 property listings across 9 countries
- Embeds them into a persistent ChromaDB vector store
- Lets you search with natural language + structured filters (country, price, bedrooms)
- Returns ranked results with relevance scores

## Data

11,960 properties scraped from the API across 9 countries:

| Country | Count |
|---------|-------|
| Spain | 7,787 |
| Cyprus | 1,478 |
| Portugal | 1,060 |
| France | 692 |
| Italy | 558 |
| USA | 184 |
| Malta | 76 |
| Switzerland | 70 |
| Greece | 55 |

## Architecture

```
properties_clean.json
        │
        ▼
scripts/build_index.py  ──►  chroma_db/  (PersistentClient, all-MiniLM-L6-v2)
        │
        ▼
scripts/search.py  ──►  search() function  ──►  ranked results
        │
        ▼
demo.py  (end-to-end demonstration)
```

- **Vector store:** ChromaDB (persistent, local — no server needed)
- **Embeddings:** `all-MiniLM-L6-v2` via ChromaDB default embedding function
- **Similarity:** Cosine distance, reported as `score = 1 - distance`

## Files

| File | Purpose |
|------|---------|
| `scrape.py` | API-based scraper for raw property data |
| `normalize_data.py` | Normalizes raw data into `properties_clean.json` |
| `scripts/check_env.py` | Verifies Python ≥ 3.11 and ChromaDB are available |
| `scripts/build_index.py` | Builds the ChromaDB vector index from `properties_clean.json` |
| `scripts/search.py` | `search()` function + CLI with filters and JSON output |
| `tests/test_search.py` | pytest verification harness for the search seam |
| `demo.py` | End-to-end demo with 3 canonical queries |
| `rag_pipeline.py` | Legacy prototype (superseded by `scripts/`) |

## Setup

Requires Python 3.11+ and ChromaDB.

```bash
pip install chromadb
python3 scripts/check_env.py   # verify environment
```

## Build the index

```bash
python3 scripts/build_index.py
```

This reads `properties_clean.json`, embeds all 11,960 properties, and writes
the vector store to `chroma_db/`. Progress prints every 100 records. Re-running
is idempotent — it deletes and rebuilds the collection.

## Search

```bash
# Natural language query
python3 scripts/search.py "3 bedroom villa in Spain with pool"

# With filters
python3 scripts/search.py --country portugal "apartment with sea views"
python3 scripts/search.py --max-price 200000 "cheap house in France"
python3 scripts/search.py --bedrooms 4 "large family home in Italy"
python3 scripts/search.py --country spain --max-price 500000 --bedrooms 3 "villa"

# JSON output (for piping)
python3 scripts/search.py --json "apartment in Spain" --limit 5

# List available countries
python3 scripts/search.py --list-countries
```

### CLI flags

| Flag | Description |
|------|-------------|
| `query` | Positional natural-language query (required) |
| `--country`, `-c` | Filter by country slug (e.g. `spain`, `france`) |
| `--min-price` | Minimum price filter |
| `--max-price`, `-p` | Maximum price filter |
| `--bedrooms`, `-b` | Minimum bedrooms |
| `--limit`, `-n` | Number of results (default 10) |
| `--json` | Output as JSON array |
| `--list-countries` | List countries in the index |

## Run the demo

```bash
python3 demo.py
```

Runs 3 canonical queries against the live index and prints formatted results.

## Tests

```bash
python3 -m pytest tests/test_search.py -v
```

The harness uses a synthetic 10-property fixture — no dependency on the full
dataset. Covers collection existence, `search()` result shape, country/price/
bedroom filters, combined filters, nonsense-query handling, and `--limit`.

## Make targets

```bash
make build     # build the ChromaDB index
make search    # run an example search
make test      # run the pytest harness
make demo      # run the end-to-end demo
make clean     # remove chroma_db/ and Python caches
```

## API source

The site exposes a REST API at
`property-portal-api-gw.youroverseashome.com/api/v1/properties/search`
with 128,311 total properties. The MVP uses an 11,960-property sample.

## Website 
A website has been created in a separate repo to demonstrate how this would work in a version of the existing website. [Homes in the Sun](website-rag-search-poc.vercel.app/)  (Homes in the Sun). It features:
    - A natural-language search POC over ~11,960 listings across multiple countries (Spain, Cyprus, Portugal, France, Italy, USA, Malta, etc.).
    - Type plain English ("Villa with pool, Costa del Sol", "Properties €300,000 and below") and it intersects all terms (AND-logic), with working price caps, sorting (price/newest), and pagination.
    - Multi-country by default; no country dropdown — relevance + natural language replace structured filters.
    
