# Design: Prompt Versioning and A/B Testing

## Problem Statement

Design a system that versions prompt templates, routes live traffic across prompt variants, and measures which variant performs best on quality and cost metrics.


## Key Requirements

- Track every prompt template change with immutable versions, authorship, and linked eval results
- Route production traffic to prompt variants with configurable split ratios and automatic rollback on degradation
- Compute statistically valid comparisons of quality, latency, and cost across variants with minimal sample waste


## Core Components

- Prompt registry: versioned store of prompt templates with metadata (model, temperature, system instructions, change description)
- Experiment config service: defines experiments (variants, traffic splits, target metrics, duration, guardrails)
- Traffic router: assigns each request to a variant deterministically by user or session, ensuring consistent experience
- Metrics collector: captures per-request signals (latency, token count, judge scores, user feedback) tagged by variant
- Analysis engine: runs sequential or fixed-horizon statistical tests and surfaces winner/loser with confidence levels


## Key Trade-offs

- Fast iteration vs. statistical rigor: smaller sample sizes let you ship faster but increase risk of false positives
- User-level vs. request-level randomization: user-level avoids inconsistent experience but needs more traffic for power
- Centralized prompt registry vs. in-code templates: a registry enables cross-team reuse but adds a dependency on an external service


## Must Explain in Interview

- How you ensure a user sees the same variant across a session (hashing user ID to variant bucket)
- Why you need guardrail metrics (safety, error rate) that can halt an experiment early even if the primary metric looks good
- How you handle prompt changes that also require a model or parameter change (bundled versioning)
- How you calculate required sample size before launching an experiment
- How rollback works: instant traffic reroute to the control variant, not a code deploy
