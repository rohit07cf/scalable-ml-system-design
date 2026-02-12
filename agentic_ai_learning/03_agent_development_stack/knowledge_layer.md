# Knowledge Layer

## What It Is

- The **external knowledge infrastructure** that gives agents access to information beyond the LLM's training data
- Core pattern: **RAG** (Retrieval-Augmented Generation) — retrieve relevant docs, inject into prompt
- Includes vector databases, knowledge graphs, and hybrid retrieval systems
- This is how agents answer questions about YOUR data, not just the internet

## Why It Matters (Interview Framing)

> "RAG is the most deployed AI pattern in production today. Interviewers will absolutely ask about chunking strategies, embedding models, reranking, and when to use a knowledge graph vs a vector DB. This is bread-and-butter for AI engineers."

---

## Knowledge Layer Architecture

```
┌──────────────────────────────────────────────────┐
│                  AGENT                            │
│  "What's our refund policy for enterprise?"       │
├──────────────────────────────────────────────────┤
│              KNOWLEDGE LAYER                      │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │  QUERY   │──▶│ RETRIEVE │──▶│   RERANK     │ │
│  │ (embed)  │   │ (top-K)  │   │ (score/filter)│ │
│  └──────────┘   └──────────┘   └──────┬───────┘ │
│                                       │          │
│  Data Sources:                        ▼          │
│  ┌──────────┐ ┌──────────┐   ┌──────────────┐   │
│  │Vector DB │ │Knowledge │   │  AUGMENT     │   │
│  │(Pinecone │ │  Graph   │   │ (inject into │   │
│  │ Weaviate │ │ (Neo4j)  │   │  LLM prompt) │   │
│  │ Chroma)  │ │          │   └──────────────┘   │
│  └──────────┘ └──────────┘                       │
├──────────────────────────────────────────────────┤
│            INGESTION PIPELINE                     │
│  Docs → Chunk → Embed → Store                    │
└──────────────────────────────────────────────────┘
```

---

## RAG (Retrieval-Augmented Generation)

### The RAG Pipeline

```
1. INGEST (offline)
   Documents → Chunker → Embedding Model → Vector DB

2. QUERY (online)
   User Query → Embed → Similarity Search → Top-K Chunks → LLM Prompt → Answer
```

### Chunking Strategies

| Strategy | How | Best For |
|---|---|---|
| **Fixed-size** | Split every N characters/tokens | Simple, fast, baseline |
| **Sentence-based** | Split on sentence boundaries | Natural text |
| **Paragraph-based** | Split on paragraph boundaries | Structured documents |
| **Semantic** | Split where topic changes (via embeddings) | Mixed-content docs |
| **Recursive** | Try largest split, recurse if too big | Code, markdown, HTML |
| **Document-aware** | Respect headers, sections, tables | Technical documentation |

💡 **Chunk size matters more than embedding model choice.** Too small = no context. Too large = noise. Start with 512-1024 tokens.

### Embedding Models

| Model | Dimensions | Speed | Quality | Cost |
|---|---|---|---|---|
| **OpenAI text-embedding-3-large** | 3072 | Fast (API) | High | $$$ |
| **OpenAI text-embedding-3-small** | 1536 | Fast (API) | Good | $$ |
| **Cohere embed-v3** | 1024 | Fast (API) | High | $$ |
| **BGE-large** | 1024 | Self-host | High | Free |
| **E5-large-v2** | 1024 | Self-host | Good | Free |

---

## Vector Databases

| Vector DB | Type | Strengths | Best For |
|---|---|---|---|
| **Pinecone** | Managed | Easiest to use, auto-scaling | Startups, fast prototyping |
| **Weaviate** | Managed/Self-host | Hybrid search, GraphQL API | Production, hybrid needs |
| **Chroma** | Embedded | Lightweight, easy local dev | Prototyping, small datasets |
| **Qdrant** | Managed/Self-host | Fast, Rust-based, filtering | Performance-critical |
| **pgvector** | PostgreSQL extension | Use existing Postgres | Teams already on Postgres |
| **Milvus** | Self-host | Billion-scale vectors | Large-scale production |

---

## Graph RAG

```
Traditional RAG:          Graph RAG:

Query → Vector Search     Query → Vector Search
     → Chunks                  → Entities + Relationships
     → LLM                     → Subgraph
                                → LLM

"What's the refund         "What's the refund policy?"
 policy?"                   → Entity: RefundPolicy
→ Chunk: "...refund..."     → Related: EnterpriseCustomer
                            → Related: 30DayWindow
                            → Related: ApprovalProcess
                            → Richer, structured context
```

**When Graph RAG > Vector RAG:**
- Data has rich relationships (org charts, product catalogs, compliance rules)
- Questions require multi-hop reasoning ("Who approved the policy that applies to enterprise customers?")
- Entities and their relationships matter more than text similarity

**When Vector RAG is sufficient:**
- Simple Q&A over documents
- Text-heavy content (articles, support docs, manuals)
- No complex relationships between entities

---

## Knowledge Graphs

```
┌─────────────┐    HAS_POLICY    ┌──────────────┐
│  Enterprise │─────────────────▶│ RefundPolicy  │
│  Customer   │                  │ (30 days)     │
└─────────────┘                  └──────┬───────┘
                                        │
                                  REQUIRES
                                        │
                                 ┌──────▼───────┐
                                 │  VP Approval  │
                                 │  (> $10K)     │
                                 └──────────────┘
```

- **Storage:** Neo4j, Amazon Neptune, ArangoDB
- **Query language:** Cypher (Neo4j), SPARQL, Gremlin
- **Strength:** Multi-hop queries, relationship traversal
- **Challenge:** Building and maintaining the graph

---

## Advanced RAG Patterns

| Pattern | Description | When to Use |
|---|---|---|
| **Naive RAG** | Simple embed → search → generate | MVP, prototype |
| **Sentence Window** | Retrieve sentence + surrounding context | Better context |
| **Parent-Child** | Retrieve child chunk, inject parent chunk | Hierarchical docs |
| **Hybrid Search** | Vector search + keyword search (BM25) | Mixed query types |
| **Reranking** | Retrieve top-50, rerank to top-5 with cross-encoder | Quality-critical |
| **Query Expansion** | Generate multiple query variants, merge results | Recall improvement |
| **Self-RAG** | Agent decides when to retrieve vs use existing context | Token efficiency |

---

## Practical Example: Enterprise Knowledge Stack

```python
# Knowledge layer configuration
knowledge_config = {
    "vector_db": {
        "provider": "pinecone",
        "index": "company-docs",
        "embedding_model": "text-embedding-3-small",
        "chunk_size": 512,
        "chunk_overlap": 50
    },
    "knowledge_graph": {
        "provider": "neo4j",
        "database": "company-ontology",
        "use_for": ["org_structure", "policy_relations", "product_catalog"]
    },
    "retrieval": {
        "strategy": "hybrid",           # Vector + BM25
        "top_k": 20,                    # Initial retrieval
        "rerank_to": 5,                 # After reranking
        "reranker": "cohere-rerank-v3"
    }
}
```

---

## Interview Questions They Will Ask

1. **"Walk me through a RAG pipeline."**
   → Ingest: docs → chunk → embed → store in vector DB. Query: embed query → similarity search → top-K chunks → inject into LLM prompt → generate answer.

2. **"How do you choose chunk size?"**
   → Depends on content type and model. Start 512-1024 tokens. Too small = lost context. Too large = noise + cost. Benchmark with your actual queries.

3. **"When would you use a knowledge graph vs a vector DB?"**
   → Vector DB: text similarity, simple Q&A. Knowledge graph: relationship queries, multi-hop reasoning, structured entities. Best systems use both (Graph RAG).

4. **"How do you improve RAG quality?"**
   → Hybrid search (vector + BM25), reranking, better chunking, query expansion, metadata filtering, evaluation with ground-truth Q&A pairs.

5. **"What is Graph RAG?"**
   → Combine vector retrieval with knowledge graph traversal. Retrieve entities and their relationships, not just text chunks. Better for complex, multi-hop queries.

---

## Common Mistakes

⚠️ **Skipping reranking** — Top-K from vector search alone often includes irrelevant results. Reranking with a cross-encoder dramatically improves precision.

⚠️ **One chunk size for all content** — Code, tables, and prose need different chunking strategies. Use document-aware chunking.

⚠️ **Not evaluating retrieval quality** — If you don't measure precision@k and recall@k, you're guessing. Build a test set of query-document pairs.

⚠️ **Ignoring metadata filtering** — Don't just search by semantic similarity. Filter by date, document type, department, access level.

⚠️ **Using RAG when the answer is in the prompt** — Self-RAG: let the agent decide whether to retrieve or use existing context. Saves latency and cost.

---

## TL;DR

- **RAG** = retrieve relevant docs, inject into LLM prompt (most common pattern)
- Key decisions: **chunk size, embedding model, vector DB, retrieval strategy**
- Use **hybrid search** (vector + BM25) + **reranking** for production quality
- **Graph RAG** for relationship-heavy, multi-hop queries
- Always **evaluate retrieval quality** with ground-truth test sets
