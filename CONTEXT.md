# CONTEXT.md — Overseas Property RAG (rag-property-search-poc)

Project glossary and current state for agents working in this repo.
Read this first. For agent-skill wiring see `AGENTS.md` and `docs/agents/`.

## Domain glossary

| Term | Meaning | Source field |
|------|---------|--------------|
| **Property / Listing** | One overseas property for sale, scraped from Your Overseas Home | `properties_clean.json` record |
| **Reference** | Stable unique ID of a listing | `id` (integer; note: raw `reference` field is unused/null) |
| **Country slug** | URL-safe country code used for filtering | `country_slug` (e.g. `spain`, `france`, `portugal`) |
| **Country name** | Human-readable country | `country_name` |
| **Location** | City / region string, e.g. `Tahoma, El Dorado County` | `location` |
| **Price** | List price in the listing's native currency | `price` + `currency` (EUR/GBP/USD/CHF) |
| **EUR price** | Price normalised to EUR for cross-country comparison | `eur_price` |
| **Price bracket** |Bucketed label, e.g. `Luxury (>€1M)` | `price_bracket` |
| **Bedrooms / Bathrooms** | Room counts | `bedrooms`, `bathrooms` |
| **Build / Plot size** | Interior / land area in m² (often null) | `build_size_m2`, `plot_size_m2` |
| **Property type** | Villa, Apartment, House, etc. | `property_type` |
| **Embedding** | Vector representation of a property's text | all-MiniLM-L6-v2 (ChromaDB default) |
| **Collection** | ChromaDB store of all property vectors | `overseas_properties` |
| **Search seam** | The `search()` function — primary tested behaviour | `scripts/search.py` |

## Architecture (single-context)

```
properties_clean.json
      │  scripts/build_index.py
      ▼
chroma_db/  (PersistentClient, cosine similarity)
      │  scripts/search.py  →  search()
      ▼
ranked results (title, price, location, country, bedrooms, bathrooms, score)
```

- **Vector store:** ChromaDB, persistent local directory `chroma_db/` (gitignored)
- **Embeddings:** `all-MiniLM-L6-v2`
- **Similarity:** cosine distance; reported as `score = 1 - distance`
- **Filters:** country (exact), price (min/max via `$gte`/`$lte`), bedrooms (min via `$gte`); combined filters wrapped in ChromaDB `$and`

## Current state (as of last session)

- ✅ All 6 MVP tickets (#2–#7) implemented, reviewed (2-stage), and merged to `main`
- ✅ 15 commits, all authored by **Robert Ojwiya <ojwiya@gmail.com>**
- ✅ Pushed to `github.com/ojwiya/rag-property-search-poc`
- ✅ All 7 GitHub issues (#1 spec + #2–#7 tickets) closed
- ✅ 12/12 pytest tests passing (`tests/test_search.py`)
- ✅ `chroma_db/` rebuilt on 2026-07-28 after the field-name fix — location data is
  now correctly populated (was stale/empty before the rebuild)

## Known gaps / follow-ups

1. **No `docs/adr/`** — decisions below are recorded inline; formal ADRs not yet extracted.
2. **`build_size_m2` / `plot_size_m2` often null** in source — size filters not reliable.
3. **Subagent delegation rate-limited** on OpenRouter free tiers; use a paid model
   (e.g. `anthropic/claude-3-haiku` via OpenRouter) for reliable subagent runs.
4. **`rag_pipeline.py`** is a legacy prototype, superseded by `scripts/` — do not extend it.

## ADRs (architecture decisions)

- **ADR-001 — ChromaDB over a server:** local `PersistentClient`, no separate vector DB
  server, to keep the MVP zero-infra.
- **ADR-002 — Normalized data is the index source:** `build_index.py` reads
  `properties_clean.json` (post-`normalize_data.py`), not the raw `properties_data.json`.
  Field names MUST match the normalized schema (`location`, `currency`, `build_size_m2`,
  `plot_size_m2`) — a past bug used raw-field names and produced empty metadata.
- **ADR-003 — `id` as deterministic document ID:** the index keys on `id` (reference
  field is null in the data); re-running `build_index.py` deletes + recreates the
  collection, so it is idempotent by rebuild, not by upsert.
- **ADR-004 — `$and` for combined filters:** ChromaDB rejects a `where` dict with
  multiple top-level operators; `search()` wraps 2+ conditions in `{'$and': [...]}` and
  passes a single condition through unchanged.
- **ADR-005 — Nonsense-query handling:** `search()` drops results with `score < 0`
  (cosine distance > 1); genuine gibberish returns `[]` rather than noise.
