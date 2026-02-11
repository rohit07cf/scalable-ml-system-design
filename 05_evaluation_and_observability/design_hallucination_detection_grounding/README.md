# Design: Hallucination Detection and Grounding

## Problem Statement

Design a system that detects when an LLM generates claims not supported by provided context and enforces grounding so responses are faithful to source material.


## Key Requirements

- Verify each factual claim in a response against retrieved source documents in real time (p99 under 500ms added latency)
- Return per-claim grounding verdicts (supported, unsupported, partially supported) with source attribution
- Support both synchronous inline checking (block ungrounded responses) and async auditing (flag for review)


## Core Components

- Claim extractor: decomposes a generated response into atomic factual claims using a lightweight model or structured prompting
- Entailment checker: scores each claim against retrieved passages using NLI models or LLM-as-judge
- Source linker: maps supported claims back to specific document chunks with span-level citations
- Decision gate: applies policy (pass-through, rewrite, block, or escalate) based on grounding scores and confidence
- Audit log and feedback loop: stores all verdicts for review, retraining entailment models, and tuning thresholds


## Key Trade-offs

- Inline checking vs. async auditing: inline adds latency but prevents ungrounded answers from reaching users; async is cheaper but reactive
- Strict grounding vs. allowing synthesis: blocking anything not verbatim in sources is safe but limits useful inference and summarization
- Dedicated NLI model vs. LLM-as-judge: NLI models are fast and cheap but less flexible; LLM judges handle nuance better but cost more


## Must Explain in Interview

- How you decompose a response into claims without losing context (claim extraction prompt design)
- Why entailment checking is not just string matching and how NLI models handle paraphrasing and negation
- How you set the grounding threshold and what happens when confidence is ambiguous (soft fallback vs. hard block)
- How you handle multi-hop claims that require reasoning across multiple source passages
- How the audit log feeds back into improving the claim extractor and entailment model over time
