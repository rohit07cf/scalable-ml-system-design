# Latency and Cost Trade-offs

## What This Covers

Reasoning about time and money in ML system design decisions.


## Key Concepts

- Latency budgets: how to allocate time across a multi-step pipeline
- Cost drivers: compute, storage, network, and per-token API pricing
- Throughput vs latency: optimizing for one often hurts the other


## Core Components

- P50 / P95 / P99 latency and why tail latency matters
- Batching strategies to improve throughput at the cost of latency
- Caching layers: prompt cache, embedding cache, result cache
- Model selection: smaller/distilled models vs frontier models
- Async vs sync execution paths and when each applies


## Key Trade-offs

- Batching for throughput vs real-time latency requirements
- Caching for speed vs staleness and memory cost
- Powerful model for quality vs smaller model for budget and speed


## Must Explain in Interview

- How to build a latency budget for a multi-model pipeline
- Why P99 latency matters more than P50 for user-facing systems
- When to use a smaller model vs a frontier model and how to decide
- How caching at different layers changes cost and freshness
- The relationship between batch size, latency, and GPU utilization
