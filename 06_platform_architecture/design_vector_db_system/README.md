# Design a Vector Database System

Design a vector database that supports approximate nearest neighbor search at scale with filtering, multi-tenancy, and low-latency queries.


## Key Requirements

- Sub-100ms p99 query latency for top-k nearest neighbor search
- Support metadata filtering combined with vector similarity
- Multi-tenant isolation with per-tenant scaling and access control


## Core Components

- Index engine: ANN algorithm (HNSW, IVF, ScaNN) with tunable recall/speed knobs
- Storage layer: vector data, metadata, and index structures on disk and in memory
- Query planner: decides filter-then-search vs search-then-filter strategy
- Partition manager: shards data by tenant, namespace, or hash for horizontal scale
- Compaction and garbage collection: reclaims space from deletes and updates


## Key Trade-offs

- HNSW (high recall, high memory) vs IVF (lower memory, tunable recall)
- Pre-filtering (smaller search space, risk of low recall) vs post-filtering (full scan, higher cost)
- In-memory indexes (fast) vs disk-based indexes (cheaper, higher latency)


## Must Explain in Interview

- How HNSW graph construction works and why it gives logarithmic query time
- Why combining filters with ANN search is fundamentally hard
- How you handle index updates without locking readers (segment-based approach)
- What happens to recall when you increase the number of partitions
- How you size memory and disk for a given document count and dimensionality
