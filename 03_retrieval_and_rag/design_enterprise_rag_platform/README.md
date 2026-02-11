# Design: Enterprise RAG Platform

## Problem Statement

Design a retrieval-augmented generation platform that lets enterprise teams ground LLM responses in internal documents with access control, freshness guarantees, and auditability.


## Key Requirements

- Serve accurate, cited answers over millions of internal documents with p99 latency under 2 seconds
- Enforce document-level and chunk-level access control so users only retrieve what they are authorized to see
- Support incremental ingestion so newly added or updated documents are retrievable within minutes


## Core Components

- Document ingestion pipeline: parse, chunk, embed, and index documents with metadata
- Vector store with filtered search (e.g., Pinecone, Weaviate, or Qdrant with metadata filtering)
- Retrieval orchestrator: query rewriting, multi-stage retrieval, and fusion
- LLM generation layer with context assembly, prompt templating, and citation extraction
- Access control service that injects permission filters into every retrieval query


## Key Trade-offs

- Chunk size vs. context quality: smaller chunks improve precision but may lose surrounding context needed for generation
- Real-time indexing vs. throughput: streaming updates reduce freshness lag but add complexity over batch re-indexing
- Single large model vs. smaller model with better retrieval: investing in retrieval quality can outperform simply scaling the LLM


## Must Explain in Interview

- How access control is enforced at query time without post-filtering (pre-filter on metadata in the vector store)
- Why you need query rewriting or expansion before retrieval and how it improves recall
- How you handle document updates: versioning chunks, tombstoning stale embeddings, incremental re-indexing
- How you assemble the retrieved context into a prompt and extract citations back to source documents
- How you evaluate the system end-to-end: retrieval recall/MRR, answer faithfulness, hallucination rate
