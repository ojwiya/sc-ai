# Building a RAG MVP with Agentic Subagents: A 6-Ticket Journey

I built a complete Retrieval-Augmented Generation pipeline over a single session — not by writing code myself, but by delegating to subagents and reviewing their work systematically. Here's what happened and what I learned about agentic development flow.

## The Goal

Scrape 11,960 overseas property listings from Your Overseas Home, build a vector index, and make them searchable via natural language with structured filters. The deliverable: a minimal but production-quality RAG MVP that proves the concept end-to-end.

## The Stack

- Python 3.14, ChromaDB (persistent local vector store, no server)
- all-MiniLM-L6-v2 embeddings
- CLI search with argsparse filters (country, price range, bedrooms)
- Pytest verification harness with 12 passing tests

The whole codebase: ~400 lines across 6 new files.

## The Agentic Flow: Subagent-Driven Development

The real engineering decision wasn't the technology — it was how I structured the work. I used the Matt Pocock development skills (`to-spec` → `to-tickets` → `implement`) with one key variation: each ticket was implemented by a fresh subagent, reviewed by two more subagents, and only advanced when both reviews passed.

The workflow for each ticket:

1. **Implementer subagent** — writes code, runs it, commits
2. **Spec reviewer subagent** — checks acceptance criteria, flags gaps
3. **Quality reviewer subagent** — checks style, error handling, bugs

If any review found issues, a fix subagent was dispatched. The cycle repeated until PASS + APPROVED. Then we moved to the next ticket in dependency order.

This is a 3-agent pipeline per ticket. Across 6 tickets, that's 18+ subagent invocations. Most completed in under 2 minutes. A few needed one fix cycle (field name mismatches and a ChromaDB filter crash cost extra rounds).

## Progress Tracking

The tracking layer was straightforward:

- **GitHub Issues** for spec + tickets, linked by number, with `ready-for-agent` labels and blocking edges declared in issue bodies
- **Todo list** in session context tracking which ticket was in progress
- **Commit hashes** — every subagent result was traceable back to a commit
- **Live transcripts** streamed to `~/.hermes/cache/delegation/live/` for real-time monitoring

No Kanban board, no project management tool. Issues + todos + commits were enough to track 6 tickets to completion in ~90 minutes.

## Why Not Other Approaches to RAG?

There are several alternative RAG architectures I considered and deliberately didn't use:

- **OpenAI embeddings + Pinecone/Weaviate** (SaaS vector DB) — adds infra cost and external dependency. For an MVP showing the concept works, local ChromaDB is zero-infra and self-contained.
- **Embedding + chunking strategies** (sentence-splitting, recursive chunking) — overkill for a demo. The property descriptions are already atomic records. We don't need to chunk them.
- **Hybrid search (BM25 + vector)** — useful for production at scale, but adds complexity. The cosine similarity alone was sufficient for relevance on this dataset.
- **Re-ranking (Cross-encoder)** — second-pass reranking improves quality but requires a separate model call. Not needed for a demo.
- **Graph-based (KG + RAG)** — property relationships could form a knowledge graph (neighborhoods → cities → countries). This is where the work heads next, and is discussed below.

Each alternative has a place. The MVP used the simplest stack that proves the concept. Complexity increases only when the data demands it.

## What Kind of Engineering Is This?

The subagent-driven, two-stage review workflow used in this project is closer to **loop engineering** than prompt engineering — but not in the way most people mean. Here's how it maps across the three paradigms:

### Prompt Engineering
The closest to prompt engineering is the **spec → ticket decomposition** step. Writing a spec is like writing a prompt for the first subagent: you define the expected behavior, inputs, outputs, and guardrails. The review step is like a second prompt ("check this against the first prompt"). But unlike pure prompt engineering, the output isn't a one-shot response — it's committed code with test coverage and traceable history.

### Loop Engineering
The development process is a **loop**: implement → review → fix → re-review → done. Each subagent invocation is an agent that does work, returns a result, and is evaluated. The review creates a feedback loop — if the result isn't right, the loop iterates with the fix. This is the same pattern as loop-based agentic systems: an agent takes an action, observes the outcome, and loops back if the observation doesn't match the goal.

What makes this distinct from simple loops is that **the loop is structural, not ad hoc**. Each ticket has defined entry (blockers done), body (implement → spec review → quality review), and exit (approved). The dependency graph of tickets creates a DAG of loops — loop engineering at the process level, not just within a single agent.

### Graph Engineering
The ticket dependency graph (6 nodes, 5 edges forming a linear chain) is the graph-engineering aspect. Tickets are nodes, blocking edges are directed dependencies, reviews are gates. This mirrors how graph-based agent systems model workflows — as DAGs where nodes are agents or tool calls and edges are data/control flow. The difference is that in this project the graph is the **development process**, not the **application logic**.

### Position on the Spectrum

| Aspect | This Project | Pure Prompt Engineering | Loop Engineering | Graph Engineering |
|--------|-------------|------------------------|------------------|-------------------|
| Workflow | Fixed pipeline (3 subagents per ticket) | Ad hoc prompts | Structured loop with gates | DAG of tickets |
| State | Stateless per subagent (fresh context) | Stateless (each prompt is independent) | Stateful via feedback (review → fix) | Stateful via graph position |
| Verification | Two reviews per ticket | None (human judges output) | Observation-based (run → check) | Traversal-based (follow deps) |
| Reproducibility | High (exact code in plan, exact review) | Low (prompt sensitivity) | Medium (depends on observation quality) | High (graph is explicit) |

This project sits closer to **loop engineering** on the spectrum. The development process is a structured loop with feedback and gates, which is what loop engineering is about. It borrows the DAG structure from graph engineering (to organize the tickets) and the prompt-precision from prompt engineering (to write specs), but the driving pattern is iterative review — a loop.

## Key Takeaways

1. **Fresh subagents per task** prevent context pollution and produce clean, self-contained work
2. **Two-stage review** (spec compliance → code quality) catches issues before they compound
3. **Bite-sized vertical slices** (one demoable behavior per ticket) keep subagents focused and reviews fast
4. **Local vector stores** (ChromaDB) are the fastest path from zero to working RAG
5. **The development process itself can be graphed** — tickets as nodes, dependencies as edges, reviews as gates

The full implementation lives at [github.com/ojwiya/sc-ai](https://github.com/ojwiya/sc-ai). 15 commits. 12 passing tests. One session, one developer (me, directing agents), zero hand-written implementation code.
