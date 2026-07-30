---
type: Plan
title: OpenWiki initialization plan
description: Temporary plan for initializing the rag-property-search-poc wiki, listing intended pages and evidence-backed relationships.
tags: [plan, openwiki-init]
---

# OpenWiki Init Plan — rag-property-search-poc

## Repository summary

A RAG (Retrieval-Augmented Generation) pipeline for overseas property listings
scraped from Your Overseas Home. Pure vector similarity search via ChromaDB
local persistent store with all-MiniLM-L6-v2 embeddings. No LLM calls during
search — zero API cost. CLI + demo + pytest harness. ~400 lines across 6 files.

## Intended wiki pages

1. `/openwiki/quickstart.md` — entrypoint: overview, setup, key concepts, links to all major concepts. Backlog at end.
2. `/openwiki/architecture.md` — the full data pipeline (scrape → normalize → build index → search), data model, ChromaDB/embedding details, ADRs, mermaid flow diagram.
3. `/openwiki/search.md` — the search seam (`search()` function), CLI flags, filter logic (`$and` combining), score handling, pytest harness, mermaid sequence diagram of a search request.

## Evidence-backed relationships (cross-links)

- quickstart.md -> links to architecture.md (describes) and search.md (describes)
- architecture.md -> scrape.py (produces raw data) -> normalize_data.py (produces clean data) -> build_index.py (produces chroma_db) -> search.py (consumes chroma_db)
- architecture.md -> search.md (search seam is the primary tested behavior; links for details)
- search.md -> tests/test_search.py (verifies the search seam)
- search.md -> architecture.md (depends on chroma_db built by build_index.py)

## Source evidence

- `/README.md` — setup, CLI, architecture diagram, file table
- `/CONTEXT.md` — domain glossary, architecture, ADRs, current state, known gaps
- `/CONTINUITY.md` — session recovery, gotchas
- `/SESSION_SUMMARY.md` — implementation history, critical issues
- `/ARTICLE.md` — engineering paradigm comparison, stack rationale
- `/scripts/search.py` — search() function, filter logic, CLI
- `/scripts/build_index.py` — index builder, format_property_text, metadata schema
- `/scripts/check_env.py` — env verification
- `/scrape.py` — API scraper
- `/normalize_data.py` — data normalizer, COUNTRY_MAP, property type detection, price brackets
- `/demo.py` — end-to-end demo
- `/tests/test_search.py` — 12-test pytest harness, synthetic fixture
- `/Makefile` — build/search/test/demo/clean targets
- `/.github/workflows/openwiki-update.yml` — scheduled OpenWiki update workflow
- `/docs/agents/` — issue tracker, triage labels, domain docs conventions
- `hermes-session-export/SESSION_NOTES.md` — rename notes, no-LLM clarification

## Open questions

- None material. All major areas are covered by existing docs and source.
