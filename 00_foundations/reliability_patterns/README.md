# Reliability Patterns

## What This Covers

Patterns that keep ML systems running when things go wrong.


## Key Concepts

- Graceful degradation: serving partial or cached results instead of failing
- Fault isolation: preventing one bad component from cascading failures
- Observability: knowing what broke and why, quickly


## Core Components

- Circuit breakers to stop calling failing downstream services
- Retries with exponential backoff and jitter
- Timeouts: per-call and end-to-end budget enforcement
- Fallback chains: primary model, secondary model, cached result, default
- Health checks and readiness probes for model serving


## Key Trade-offs

- Aggressive retries for reliability vs retry storms that worsen outages
- Strict timeouts for latency vs cutting off slow but valid responses
- Complex fallback logic for uptime vs added code paths to maintain and test


## Must Explain in Interview

- How a circuit breaker works and when it trips open vs closes
- Why retries need jitter and what happens without it
- How to design a fallback chain for an LLM-powered feature
- The difference between a health check and a readiness probe
- How to set timeout budgets across a multi-service pipeline
