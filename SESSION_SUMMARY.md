# Session Summary — 2026-07-28

## Overview

Completed implementation of the `sc-ai` MVP (Overseas Property RAG) — a ChromaDB-backed pipeline for searching overseas property listings via natural language.

## Starting point

Resumed session `20260727_224952_61838d`. The spec was published (GitHub issue #1), Matt Pocock engineering skills were configured (issue tracker, triage labels, domain docs at `docs/agents/`), 6 implementation tickets (#2–#7) were created with `ready-for-agent` labels, and `IMPLEMENTATION_PLAN.md` (985 lines, 8 tasks) already existed.

## Model/Config

- Parent model: `moonshotai/kimi-k3` via Nous Portal
- Subagent delegation model was changed multiple times due to OpenRouter rate limits on free tiers. Final subagent model: `inclusionai/ling-3.0-flash:free` (Nous Portal)

## Tickets Completed

| # | Title | File | Commits | Review cycles |
|---|-------|------|---------|---------------|
| 2 | Environment verification script | `scripts/check_env.py` | 2 | 3 (implement → spec fix → PASS) |
| 3 | Build ChromaDB index | `scripts/build_index.py` | 3 | 3 (implement → spec fix batch_size + spec fix field-names → PASS) |
| 4 | Search function and CLI | `scripts/search.py` | 3 | 4 (implement → spec gap: `$and` + score threshold → spec re-review → PASS → QUAL request: field names → fix → PASS) |
| 5 | Verification harness | `tests/test_search.py` | 2 | 3 (implement → spec review PASS → qual request: CLI tests bypass fixture → fix → PASS) |
| 6 | End-to-end demo | `demo.py` | 1 | 2 (implement → spec review; review hit HTTP 400, manual verification passed) |
| 7 | Documentation | `README.md`, `Makefile` | 1 | manual |

## Critical Issues Surfaced by Two-Stage Review

1. **Field name mismatch** — `build_index.py` used raw API field names (`locationName`, `currencyCode`, `buildSize`, `plotSize`) instead of the normalized schema (`location`, `currency`, `build_size_m2`, `plot_size_m2`). Caused empty metadata in the ChromaDB index. Fixed in commit `b22275b`.

2. **Stale index** — The existing `chroma_db/` was built before the field-name fix. All 11,960 records had empty `location`. Rebuilt index (`chroma_db/`) was regenerated with correct data.

3. **Combined ChromaDB filter crash** — Multiple top-level `where` conditions caused `ValueError`. Fixed by wrapping in `$and` (ADR-004). Commits `7235337`, `823933f`.

4. **Nonsense query noise** — `score > 0` threshold too aggressive for cosine distance (scores range -1 to 1). Relaxed to `score >= 0`. Commit `823933f`.

5. **CLI tests bypassed fixture** — `TestCLI` used `subprocess.run()` which spawns a fresh process unaware of fixture monkey-patching. Removed `TestCLI` class, kept `TestSearchFunction` and `TestCollection`. Commit `ddd8ab2`.

## Git Author Fix

Commits 1–10 were authored as `Paul <phanminh65@gmail.com>` (misconfigured repo). Fixed:
```bash
git filter-branch -f --env-filter '
export GIT_AUTHOR_NAME="Robert Ojwiya"
export GIT_AUTHOR_EMAIL="ojwiya@gmail.com"
export GIT_COMMITTER_NAME="Robert Ojwiya"
export GIT_COMMITTER_EMAIL="ojwiya@gmail.com"
' c00edf6..HEAD
```
Also fixed `git config user.name` and `user.email`. All 15 commits now show `Robert Ojwiya <ojwiya@gmail.com>`.

## Push to GitHub

Remote was behind local (3 Paul-authored commits). Force-pushed local `main` to `origin/main`:
```
git push -u origin main --force
```
All 7 GitHub issues (#1–#7) closed.

## Key Documentation Added

- `CONTEXT.md` — Domain glossary (16 terms), architecture diagram, current state, 5 ADRs
- `README.md` — Comprehensive (setup, architecture, CLI flags, Make targets, data counts)
- `Makefile` — `make build`, `make search`, `make test`, `make demo`, `make clean`

## Final State

- 15 commits on `main`, all authored by Robert Ojwiya
- Pushed to `github.com/ojwiya/sc-ai`
- 12/12 pytest tests passing
- 7 GitHub issues (spec + 6 tickets), all closed
- `chroma_db/` rebuilt with correct field names (local, gitignored)
- Repo is handoff-ready with Matt Pocock skills configured