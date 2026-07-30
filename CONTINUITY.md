# Continuity Guide — sc-ai Project

## Picking Up in a New Session

### Step 1: Check where we left off

```bash
# Current state
cd /Users/admin/Documents/sc-ai          # project root (not default home dir)
git log --oneline -3                     # recent commits
make test                                # health check — should say 12 passed
python3 scripts/search.py "villa in Spain with pool" --limit 3   # smoke test
```

### Step 2: Understand the project

- **Project**: `sc-ai` — Overseas Property RAG pipeline (GitHub: `ojwiya/sc-ai`)
- **Data**: 11,960 properties across 9 countries in `properties_clean.json`
- **Vector store**: ChromaDB at `chroma_db/` (gitignored, must be rebuilt after code changes)
- **Key code**: `scripts/build_index.py`, `scripts/search.py`, `tests/test_search.py`
- **Docs**: `README.md`, `CONTEXT.md`, `ARTICLE.md`, `SESSION_SUMMARY.md`

### Step 3: Resume the session

In Hermes: `hermes --resume <session_id>` or just start a new session and reference this guide
In Claude Code: `claude -c` in the project directory

## Session History Summary

| Phase | What | Status |
|-------|------|--------|
| Spec | Published GitHub issue #1 | ✅ Closed |
| Tickets | 6 tickets (#2–#7) created with blocking edges | ✅ All closed |
| #2 | `scripts/check_env.py` | ✅ Complete |
| #3 | `scripts/build_index.py` | ✅ Complete (rebuilt with correct field names) |
| #4 | `scripts/search.py` (search + CLI) | ✅ Complete |
| #5 | `tests/test_search.py` (12 tests) | ✅ Complete |
| #6 | `demo.py` (3 queries) | ✅ Complete |
| #7 | `README.md` + `Makefile` | ✅ Complete |
| Docs | `CONTEXT.md`, `ARTICLE.md`, `SESSION_SUMMARY.md` | ✅ Complete |
| Push | Force-pushed to `github.com/ojwiya/sc-ai` | ✅ Done |

## Key Files for Continuity

- **`IMPLEMENTATION_PLAN.md`** — original 8-task plan (985 lines)
- **`CONTEXT.md`** — domain glossary, architecture, ADRs
- **`SESSION_SUMMARY.md`** — detailed session record with ticket-by-ticket breakdown
- **`ARTICLE.md`** — LinkedIn article with references

## Gotchas

1. **Stale index**: If you change `build_index.py`, delete `chroma_db/` first — the index is not auto-rebuilt
2. **Field names**: Must use normalized schema (`location`, `currency`, `build_size_m2`, `plot_size_m2`, `id`) — not raw API names
3. **SSH blocked**: Use `gh` CLI (HTTPS) for all GitHub operations
4. **Free model rate limits**: OpenRouter free models (`*.free`) are rate-limited for subagent delegation; use a paid model or Novita key for reliable subagents
5. **Author**: All commits authored by Robert Ojwiya <ojwiya@gmail.com>

## If You Need to Continue Development

The Matt Pocock skills are configured (`AGENTS.md` → `docs/agents/`):
- `to-spec` — publish a new spec to GitHub Issues
- `to-tickets` — break the spec into tracer-bullet tickets
- `implement` — execute tickets via subagent-driven development with two-stage review

## Environment

- Repo: `/Users/admin/Documents/sc-ai`
- Python: 3.14 at `/usr/local/bin/python3`
- ChromaDB: 1.5.9
- Git remote: `https://github.com/ojwiya/sc-ai.git` (HTTPS, gH keyring)
- Hermes profiles: `~/.hermes/profiles/default/`
- Config: `~/.hermes/config.yaml` (delegation.model = deepseek/deepseek-v4-pro; delegation.provider = openrouter)
