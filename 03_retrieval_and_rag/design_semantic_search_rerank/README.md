# Design: Semantic Search with Reranking

## Problem Statement

Design a two-stage retrieval system that uses fast approximate nearest neighbor search to fetch candidates, then applies a cross-encoder reranker to produce a high-precision final ranking.


## Key Requirements

- First stage retrieves top-100 candidates from millions of documents in under 20ms using ANN search
- Second stage reranks candidates with a cross-encoder model and returns top-10 results within 150ms total
- Support online model updates for the reranker without downtime or index rebuilds


## Core Components

- Bi-encoder embedding model that maps queries and documents to a shared vector space for fast retrieval
- ANN index (HNSW, IVF, or ScaNN) for sub-linear first-stage retrieval
- Cross-encoder reranker that scores each (query, document) pair jointly for high-precision reranking
- Embedding precomputation pipeline: offline batch encoding of the document corpus
- Model serving layer with batched inference, caching, and fallback to first-stage results on timeout


## Key Trade-offs

- Bi-encoder speed vs. cross-encoder accuracy: bi-encoders allow precomputation but miss fine-grained query-document interaction
- Reranker depth (top-k to rerank) vs. latency: reranking more candidates improves recall but increases latency linearly
- Distillation vs. full cross-encoder: distilling the reranker into a smaller model reduces latency but may lose tail-query accuracy


## Must Explain in Interview

- Why a two-stage architecture is necessary: you cannot run a cross-encoder over millions of documents at query time
- How bi-encoder training works (contrastive loss, hard negatives) and why hard negative mining matters
- What a cross-encoder does differently: full attention over the concatenated query-document pair instead of independent encoding
- How you decide the rerank depth (top-k) and its impact on the recall-latency trade-off
- How you measure reranker quality: NDCG, MRR, and offline/online evaluation with interleaving experiments
