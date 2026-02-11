# Design: AI Code Assistant

## Problem Statement

Design an inline coding assistant that provides autocomplete, generation, explanation, and refactoring across a large codebase.


## Key Requirements

- Autocomplete latency under 200ms for inline suggestions to avoid disrupting developer flow
- Codebase-aware: suggestions must respect project conventions, imports, and types
- Support multiple interaction modes: autocomplete, chat, inline edit, test generation


## Core Components

- Context assembly engine gathering relevant code (open files, imports, recent edits, repo-wide symbols)
- Fast completion model for low-latency autocomplete, frontier model for complex generation tasks
- Code retrieval index over the repository: function signatures, docstrings, usage patterns
- Post-processing layer: syntax validation, linting, import resolution, deduplication
- Evaluation pipeline: acceptance rate tracking, functional correctness tests, user feedback signals


## Key Trade-offs

- Small/fast model for autocomplete speed vs large model for complex reasoning tasks
- Repository-wide indexing for better context vs incremental indexing for freshness
- Speculative multi-suggestion generation vs single best suggestion for UX simplicity


## Must Explain in Interview

- How you assemble context from a large repo into a limited prompt window (what to include, what to skip)
- Why you need two model tiers (fast + powerful) and how you route between them
- How you keep the code index fresh as developers edit files in real time
- How you measure quality: acceptance rate, edit distance after accept, functional correctness (pass@k)
- How you handle security: preventing secrets in suggestions, license-aware filtering, prompt injection
