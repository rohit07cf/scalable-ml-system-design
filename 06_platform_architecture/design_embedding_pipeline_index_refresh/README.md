# Design an Embedding Pipeline with Index Refresh

Design a system that continuously converts documents into embeddings and keeps a vector index fresh as source data changes.


## Key Requirements

- Process new, updated, and deleted documents with minimal index staleness
- Support multiple embedding models and index types across use cases
- Handle millions of documents without re-embedding the entire corpus on each update


## Core Components

- Change data capture (CDC): detects inserts, updates, deletes from source systems
- Chunking service: splits documents into retrieval-friendly segments
- Embedding service: batches chunks through the embedding model (GPU or API)
- Index writer: upserts and deletes vectors in the target vector store
- Freshness monitor: tracks lag between source change and index availability


## Key Trade-offs

- Incremental updates (low latency) vs full re-index (consistency, simpler logic)
- Inline embedding on write path vs async batch pipeline
- Single global index vs per-tenant indexes (isolation vs operational overhead)


## Must Explain in Interview

- How CDC captures deletes and why delete propagation to the index is non-trivial
- Why chunk boundaries matter for retrieval quality and how you version them
- How you handle embedding model upgrades without serving mixed-version vectors
- What backpressure strategy you use when the embedding service falls behind
- How you measure index freshness SLA and alert on staleness
