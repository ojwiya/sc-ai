# rag-property-search-poc — Overseas Property RAG

RAG pipeline for searching overseas property listings scraped from Your Overseas Home.

## Quick Start

```bash
cd /Users/admin/Documents/sc-ai
pip install chromadb
python3 scripts/build_index.py     # build the vector index (11,960 properties, ~4.5 min)
python3 scripts/search.py "villa in Spain"  # search
python3 demo.py                    # end-to-end demo
```

## Key Files

| File | Purpose |
|------|---------|
| `scripts/build_index.py` | Builds ChromaDB index from properties_clean.json |
| `scripts/search.py` | search() function + CLI with filters and JSON output |
| `scripts/check_env.py` | Verifies Python ≥ 3.11 and ChromaDB are available |
| `tests/test_search.py` | Pytest harness (12 tests, uses synthetic fixture) |
| `demo.py` | End-to-end demo with 3 canonical queries |
| `README.md` | Full documentation |
| `Makefile` | build, search, test, demo, clean targets |
| `CONTEXT.md` | Domain glossary, architecture, ADRs |

## Architecture

- Vector store: ChromaDB (persistent local, `chroma_db/`, gitignored)
- Embeddings: all-MiniLM-L6-v2 (ChromaDB default)
- Similarity: cosine distance, reported as `score = 1 - distance`
- Filters: country (exact), price range (`$gte`/`$lte`), bedrooms (`$gte`), combined via `$and`

## Data

Source: `properties_clean.json` (normalized from raw `properties_data.json`)
10 fields: `id`, `title`, `location`, `country_slug`, `country_name`, `price`, `currency`, `bedrooms`, `bathrooms`, `build_size_m2`, `plot_size_m2`, `eur_price`, `price_bracket`, `description`, `url`, `image_count`, etc.

Note: `country_slug` (not `country`), `location` (not `locationName`), `currency` (not `currencyCode`), `build_size_m2` (not `buildSize`), `plot_size_m2` (not `plotSize`), `id` (not `reference`).

## Important Notes

- `chroma_db/` must be rebuilt after changes to `build_index.py` (delete `chroma_db/` and re-run `make build`)
- The vector index was rebuilt on 2026-07-28 after a field-name fix — the old stale index is gone
- All 15 git commits are authored by Robert Ojwiya <ojwiya@gmail.com>
- Push to GitHub: `git push` (uses gH CLI HTTPS credential)
- SSH is blocked by firewall; use `gh` CLI or HTTPS for remote operations

## Testing

```bash
python3 -m pytest tests/test_search.py -v   # 12 tests
make test
```

## Claude Code Integration

Run searches directly:
```bash
claude -p "Refactor the search filter logic" --workdir /Users/admin/Documents/sc-ai --allowedTools Read,Edit,Bash
```

Interactive session:
```bash
cd /Users/admin/Documents/sc-ai && claude
```
