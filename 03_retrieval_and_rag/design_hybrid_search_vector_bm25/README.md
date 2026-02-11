# Design: Hybrid Search (Vector + BM25)

## Problem Statement

Design a search system that combines dense vector retrieval with sparse lexical (BM25) retrieval to improve recall and robustness across diverse query types.


## Key Requirements

- Return top-k results that satisfy both semantic similarity and keyword relevance within 100ms at p95
- Handle queries where one signal dominates: exact keyword matches, conceptual similarity, or both
- Scale to tens of millions of documents with independent indexing for each retrieval path


## Core Components

- BM25 index (e.g., Elasticsearch or OpenSearch) for sparse lexical retrieval
- Vector index (e.g., HNSW-based ANN store) for dense semantic retrieval
- Query encoder that produces both a text query for BM25 and a dense embedding for vector search
- Fusion layer that merges two ranked lists (reciprocal rank fusion, weighted scoring, or learned combination)
- Relevance feedback loop: click-through and engagement signals to tune fusion weights over time


## Key Trade-offs

- Early fusion vs. late fusion: merging at the score level is simpler but less expressive than a learned reranker over both candidate sets
- Symmetric weighting vs. query-dependent weighting: fixed alpha is easy to tune but query-adaptive mixing handles diverse intents better
- Maintaining two indexes vs. a single hybrid index: separate indexes are flexible but double the storage and operational cost


## Must Explain in Interview

- Why BM25 and vector search are complementary: BM25 excels at exact term matches and rare tokens; vectors capture paraphrase and semantic similarity
- How reciprocal rank fusion works and why it is a strong default when you lack training data for a learned merger
- How you handle the cold-start problem for fusion weights before you have click data
- Why sparse retrieval often outperforms dense retrieval on out-of-domain or tail queries
- How you evaluate hybrid search: per-signal recall, fused recall, and A/B testing downstream task metrics
