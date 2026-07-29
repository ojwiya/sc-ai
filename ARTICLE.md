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

## RAG → Loops → Graphs

This project sits at a specific point in a broader engineering evolution: from RAG, to looping, to graph-based reasoning.

**RAG** (this project) is retrieval + generation. You query a vector store, get relevant documents, pass them to a model with a prompt. It's stateless — each query is independent. The search seam (`search()` function) is the single ideal boundary for testing.

**Loops** add state. An agent that retrieves, reasons, acts, observes, and loops back is doing agentic RAG — not just one-shot retrieval. Think: "find properties under €200k in Portugal, then compare the top 3, then draft a summary." Each step is a tool call; the sequence forms an execution loop.

**Graphs** add structure to both knowledge and execution. A property knowledge graph links listings to neighborhoods, neighborhoods to cities, cities to regions, regions to countries. Queries traverse the graph. Execution graphs define agent workflows as DAGs with dependencies, retries, and branching. This project uses a flat vector store (no relational structure between properties). The next evolution is embedding graph relationships into the vector store (neighborhood embeddings, similarity clusters) or adding an explicit graph layer on top.

The agentic subagent workflow itself mirrors a loop-graph structure: each ticket is a node, dependencies are edges, reviews are gates, and the whole pipeline is a directed acyclic graph of subagent invocations. The framework handled this naturally — it's loop/graph engineering applied to the development process itself, not just the application.

## Key Takeaways

1. **Fresh subagents per task** prevent context pollution and produce clean, self-contained work
2. **Two-stage review** (spec compliance → code quality) catches issues before they compound
3. **Bite-sized vertical slices** (one demoable behavior per ticket) keep subagents focused and reviews fast
4. **Local vector stores** (ChromaDB) are the fastest path from zero to working RAG
5. **The development process itself can be graphed** — tickets as nodes, dependencies as edges, reviews as gates

The full implementation lives at [github.com/ojwiya/sc-ai](https://github.com/ojwiya/sc-ai). 15 commits. 12 passing tests. One session, one developer (me, directing agents), zero hand-written implementation code.
