# Design: Multi-Embedding Retrieval

## Problem Statement

Design a retrieval system that generates and indexes multiple embedding representations per document (e.g., title, body, summary, entity-level) and routes or fuses across them at query time for improved recall.


## Key Requirements

- Support multiple embedding spaces per document, each capturing a different semantic aspect (title, passage, summary)
- Route queries to the most relevant embedding space or fuse results across spaces with bounded latency overhead
- Allow independent updates to individual embedding types without full re-indexing of the corpus


## Core Components

- Multi-encoder pipeline: separate or shared-backbone models that produce distinct embeddings per document field
- Per-field ANN indexes: independent vector indexes for each embedding type (title index, passage index, etc.)
- Query router or classifier that predicts which embedding spaces are most relevant for a given query
- Fusion layer that merges candidate lists from multiple indexes (weighted RRF, learned scoring, or cascade)
- Embedding versioning store: tracks which model version produced each embedding for safe rollouts and rollbacks


## Key Trade-offs

- Shared backbone with projection heads vs. fully separate models: shared backbone is cheaper but may underperform on specialized fields
- Always-query-all-indexes vs. selective routing: querying all indexes maximizes recall but increases latency and cost linearly
- Per-field embeddings vs. a single embedding over concatenated fields: single embedding is simpler but loses fine-grained field-level signal


## Must Explain in Interview

- Why a single embedding per document is often insufficient: title-level and passage-level semantics differ and a single vector averages them out
- How query routing works: a lightweight classifier or heuristic that selects 1-2 indexes to query based on query type
- How you handle embedding model upgrades: versioned embeddings, shadow indexing, and gradual migration
- The latency model: parallel fan-out to multiple indexes, merge results, and how to set timeouts per index
- How you evaluate multi-embedding retrieval: per-index recall, fused recall, and ablation studies removing individual embedding types
