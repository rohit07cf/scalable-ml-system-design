# Memory Systems

## What It Is

- **Memory** gives agents the ability to retain and recall information across reasoning steps and sessions
- Without memory, every LLM call starts from zero — no context, no learning
- Memory is what makes an agent feel "intelligent" vs "amnesic"
- Four types: short-term, long-term, vector (RAG), and workspace memory

## Why It Matters (Interview Framing)

> "Memory design is a top interview differentiator. Everyone can build a ReAct loop. The hard part is: how does your agent remember what it did 5 steps ago? How does it learn across sessions? That's where memory architecture matters."

---

## Simple Mental Model

> **Short-term memory** = your whiteboard during a meeting
> **Long-term memory** = your personal notes app
> **Vector memory** = your company's search engine
> **Workspace memory** = the files open on your desktop right now

---

## The Four Memory Types

```
┌────────────────────────────────────────────────────────┐
│                    AGENT MEMORY                         │
├──────────────┬──────────────┬────────────┬─────────────┤
│  SHORT-TERM  │  LONG-TERM   │   VECTOR   │  WORKSPACE  │
│  (Working)   │  (Semantic)  │   (RAG)    │  (Session)  │
├──────────────┼──────────────┼────────────┼─────────────┤
│ Current task │ Past sessions│ Knowledge  │ Files, code │
│ context      │ User prefs   │ base docs  │ artifacts   │
│              │ Learned facts│ Embeddings │             │
├──────────────┼──────────────┼────────────┼─────────────┤
│ In-context   │ External DB  │ Vector DB  │ File system │
│ (prompt)     │ (Redis/PG)   │(Pinecone)  │ (local/S3)  │
├──────────────┼──────────────┼────────────┼─────────────┤
│ Volatile     │ Persistent   │ Persistent │ Session-    │
│              │              │            │ scoped      │
└──────────────┴──────────────┴────────────┴─────────────┘
```

---

### 1. Short-Term Memory (Working Memory)

**What:** The conversation history and scratchpad within the current agent execution.

```
┌─────────────────────────────────┐
│      LLM Context Window         │
│                                 │
│  System prompt                  │
│  + User goal                    │
│  + Step 1: Thought + Action     │
│  + Step 1: Observation          │
│  + Step 2: Thought + Action     │  ← THIS is short-term memory
│  + Step 2: Observation          │
│  + Step 3: Thought + ...        │
│                                 │
│  [TOKEN LIMIT]                  │
└─────────────────────────────────┘
```

- **Storage:** In the LLM's context window (prompt)
- **Lifetime:** Current execution only
- **Limit:** Token window (4K–200K depending on model)
- **Challenge:** Context window overflow on long tasks

**Solutions for overflow:**
- Sliding window (drop oldest messages)
- Summarization (compress old steps into summary)
- Hierarchical (keep summary + last N steps)

---

### 2. Long-Term Memory (Semantic Memory)

**What:** Persistent facts, user preferences, and learned information across sessions.

```
Agent Session 1:            Agent Session 2:
  "User prefers Python"  →   Retrieve: "User prefers Python"
  Save to long-term DB       Use in response
```

- **Storage:** External database (Redis, PostgreSQL, DynamoDB)
- **Lifetime:** Permanent (or TTL-based)
- **Access:** Queried at start of session or on-demand
- **Format:** Key-value, structured JSON, or natural language

**Example schema:**
```json
{
  "user_id": "u_123",
  "memories": [
    {"fact": "Prefers Python over JS", "confidence": 0.9, "created": "2025-01-15"},
    {"fact": "Works at Acme Corp, ML team", "confidence": 0.95, "created": "2025-02-01"},
    {"fact": "Timezone: PST", "confidence": 1.0, "created": "2025-02-01"}
  ]
}
```

---

### 3. Vector Memory (RAG)

**What:** External knowledge retrieved via semantic similarity search.

```
Query: "How to configure SSL?"
    │
    ▼
┌──────────┐     ┌────────────────┐     ┌──────────┐
│ Embed    │────▶│  Vector DB     │────▶│ Top-K    │
│ query    │     │  (similarity   │     │ results  │
│          │     │   search)      │     │          │
└──────────┘     └────────────────┘     └──────────┘
                                              │
                                              ▼
                                    Inject into LLM prompt
```

- **Storage:** Vector database (Pinecone, Weaviate, Chroma, Qdrant)
- **Content:** Company docs, knowledge base, past conversations
- **Access:** Semantic search (not keyword match)
- **Key metric:** Retrieval relevance (precision@k, recall@k)

💡 **RAG is the most common memory pattern in production agents.**

---

### 4. Workspace Memory

**What:** Files, artifacts, and intermediate outputs created during the current task.

- Code files being edited
- Reports being drafted
- Data files being analyzed
- Scratchpad notes

- **Storage:** Local filesystem, S3, temp directory
- **Lifetime:** Session-scoped (cleaned up after task completion)
- **Access:** File read/write tools

---

## Choosing Memory Types

| Scenario | Memory Type |
|---|---|
| Agent needs context from 3 steps ago | **Short-term** (in-context) |
| Remember user prefers dark mode | **Long-term** (persistent DB) |
| Look up company HR policy | **Vector** (RAG) |
| Edit a code file across multiple steps | **Workspace** |
| Agent needs to recall what failed yesterday | **Long-term** |
| Search through 10,000 support tickets | **Vector** |

---

## Practical Example: Customer Support Agent Memory

```python
class AgentMemory:
    def __init__(self, user_id):
        # Short-term: conversation buffer
        self.conversation = []

        # Long-term: load user profile
        self.user_profile = redis.get(f"user:{user_id}:memory")

        # Vector: connect to knowledge base
        self.kb = PineconeIndex("support-docs")

        # Workspace: temp files for this session
        self.workspace = TempDirectory()

    def get_context(self, query):
        """Build context for LLM from all memory types"""
        return {
            "conversation": self.conversation[-10:],     # Last 10 turns
            "user_facts": self.user_profile.facts,       # Known preferences
            "relevant_docs": self.kb.search(query, k=3), # Top 3 KB articles
            "workspace_files": self.workspace.list()      # Current artifacts
        }
```

---

## Interview Questions They Will Ask

1. **"How do you handle context window limits in a long-running agent?"**
   → Sliding window, summarization, hierarchical memory. Move older context to external storage, keep summaries in-context.

2. **"Explain the difference between short-term and long-term memory in agents."**
   → Short-term = in-context (prompt), volatile, limited by token window. Long-term = external DB, persistent, unlimited.

3. **"How does RAG fit into agent memory?"**
   → RAG is vector memory — external knowledge retrieved by semantic similarity. It's how agents access large knowledge bases without stuffing everything into the prompt.

4. **"How would you implement memory for a multi-session agent?"**
   → Long-term memory in a persistent store. Save key facts, user preferences, and task outcomes. Load at session start.

5. **"What happens when the context window fills up?"**
   → Oldest messages are dropped or summarized. Critical info should be persisted to long-term memory before eviction.

---

## Common Mistakes

⚠️ **Stuffing everything into the prompt** — Context windows are limited and expensive. Use external memory for large datasets.

⚠️ **No memory eviction strategy** — Without summarization or sliding window, the agent hits token limits and crashes.

⚠️ **Treating RAG as "done"** — Retrieval quality directly impacts agent quality. Bad retrieval = bad answers. Tune chunk size, embedding model, reranking.

⚠️ **Not persisting important facts** — If the agent learns something important, save it to long-term memory. Don't rely on the conversation buffer.

⚠️ **Ignoring memory in multi-agent systems** — Agents sharing memory need coordination. Race conditions, stale reads, and conflicting updates are real.

---

## TL;DR

- **Short-term** = conversation context in the prompt (volatile, token-limited)
- **Long-term** = persistent facts in external DB (Redis, PostgreSQL)
- **Vector (RAG)** = semantic search over knowledge base (Pinecone, Weaviate)
- **Workspace** = files and artifacts for the current session
- **Key challenge:** context window overflow → solve with summarization + external storage
