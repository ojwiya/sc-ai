# Session Notes — rag-property-search-poc
## July 30, 2026

### Repo Rename
- Renamed from `sc-ai` to `rag-property-search-poc`
- GitHub: `ojwiya/rag-property-search-poc`
- All `sc-ai` / `ojwiya/sc-ai` / `github.com/ojwiya/sc-ai` references updated across docs

### Paul/phanminh Cleanup
- Rewrote git history via `git filter-branch` to fix Paul-authored commit (c00edf6) → Robert Ojwiya
- Removed 4 Paul references from CONTEXT.md, CONTINUITY.md, SESSION_SUMMARY.md
- Stale git global config (user.name=Paul, user.email=phanminh65@gmail.com) cleaned up
- Empty commit pushed to nudge GitHub contributor graph re-index

### Key Architecture Notes
- No LLM calls made during RAG search — ChromaDB uses ONNX MiniLM (`all-MiniLM-L6-v2`) locally via ONNX runtime
- Queries embedded client-side, matched with cosine similarity — zero API cost, zero external deps
- OpenRouter models (`deepseek/deepseek-v4-pro`, `inclusionai/ling-3.0-flash:free`) used only for subagent delegation

### Cost
- MVP runs entirely on free-tier OpenRouter or local ChromaDB
- Paid model (deepseek-v4-pro) needed only if using `delegate_task` for subagent dispatch
- No .env file, no API keys stored in repo

### Key Files
- `scripts/build_index.py` — builds ChromaDB index from properties JSON
- `scripts/search.py` — pure vector similarity search, no LLM calls
- `scripts/check_env.py` — validates environment
- `ARTICLE.md` — detailed write-up of the session and architecture
- `CHANGES.md` — changelog of the rename and cleanup
