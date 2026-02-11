# Design: Large Document Summarization

## Problem Statement

Design a system that produces faithful, structured summaries of documents ranging from 10 pages to 500+ pages.


## Key Requirements

- Handle documents far exceeding a single model's context window
- Summaries must be factually faithful: no hallucinated facts, no omitted key points
- Support multiple output formats: executive summary, section-by-section, Q&A-style


## Core Components

- Document ingestion pipeline: parsing PDFs/DOCX, extracting structure (headings, tables, figures)
- Chunking strategy that respects document structure (sections, paragraphs) not just token counts
- Map-reduce or hierarchical summarization engine for long documents
- Faithfulness verification layer comparing summary claims against source chunks
- Output formatter producing structured, navigable summaries with source references


## Key Trade-offs

- Map-reduce (scalable, parallelizable) vs iterative refinement (higher coherence, sequential)
- Aggressive compression for brevity vs verbose output to avoid information loss
- Using full long-context models (simpler pipeline) vs chunked approaches (cheaper, more controllable)


## Must Explain in Interview

- How you handle a 500-page document that exceeds any model's context window
- The difference between extractive, abstractive, and hybrid summarization and when each applies
- How you detect and prevent hallucination in summaries (faithfulness metrics, entailment checks)
- Why chunking strategy matters: section-aware vs fixed-size and the downstream effects on quality
- How you evaluate summary quality at scale: ROUGE limitations, LLM-as-judge, human eval tradeoffs
