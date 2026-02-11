# Design: Conversation Memory System

Design a memory system that gives LLM agents access to relevant past context across turns, sessions, and users while staying within token and latency budgets.


## Key Requirements

- Support short-term (in-session), long-term (cross-session), and shared (cross-user/org) memory tiers
- Retrieve relevant memories within strict latency and token budgets per LLM call
- Memories must be writeable by agents, editable by users, and subject to retention policies


## Core Components

- **Memory Writer** -- extracts and stores salient facts, summaries, and user preferences from conversations
- **Tiered Store** -- hot cache for current session, warm vector store for recent history, cold archive for long-term
- **Retrieval Engine** -- hybrid search (recency + semantic similarity + importance score) to select memories for injection
- **Context Assembler** -- packs retrieved memories into the prompt within a token budget, with priority ordering
- **Retention and Forget Service** -- TTL-based expiry, user-triggered deletion, and compliance-driven purging


## Key Trade-offs

- Verbatim storage (precise, large) vs. summarized storage (compact, lossy)
- Eager memory writes every turn (complete, high write load) vs. selective extraction (lighter, may miss context)
- Per-user isolation (simple privacy) vs. shared memory pools (better for teams, harder access control)


## Must Explain in Interview

- How you decide what to extract and store vs. what to discard after each turn
- How the retrieval engine ranks and selects memories when the candidate set exceeds the token budget
- How you handle memory staleness and contradiction (e.g., user corrects a previously stored fact)
- How you enforce per-user data isolation and comply with deletion requests across all tiers
- How you measure memory quality (retrieval precision, downstream task improvement, user satisfaction)
