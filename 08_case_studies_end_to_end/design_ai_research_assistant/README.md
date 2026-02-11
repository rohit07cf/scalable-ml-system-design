# Design: AI Research Assistant

## Problem Statement

Design a system that helps researchers find, synthesize, and reason over large collections of academic papers and technical documents.


## Key Requirements

- Multi-step research workflows: search, read, compare, synthesize across dozens of sources
- Accurate citation and attribution for every claim in generated output
- Support for iterative refinement: users narrow or expand scope mid-session


## Core Components

- Agentic orchestrator that plans multi-step research tasks and manages tool calls
- Hybrid retrieval over structured metadata (authors, dates, venues) and unstructured full-text
- Citation extraction and linking module that grounds every output sentence to source spans
- Synthesis engine that produces structured summaries, comparisons, and literature reviews
- User workspace storing session state, saved searches, and annotated results


## Key Trade-offs

- Deep single-paper analysis vs broad multi-paper synthesis within a single query budget
- Real-time retrieval from live sources vs pre-indexed corpus for speed and consistency
- Agentic multi-step reasoning for thoroughness vs single-pass generation for latency and cost


## Must Explain in Interview

- How the agent decides when to search, when to read deeper, and when to stop gathering evidence
- How you implement citation grounding: mapping generated claims back to specific source passages
- How you handle contradictory information across multiple papers
- Why evaluation is hard here and what proxy metrics you would use (citation accuracy, factual consistency)
- How you manage token cost when synthesizing across 50+ documents in a single session
