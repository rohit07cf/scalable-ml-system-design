# Design a Feature Store for Personalization

Design a feature store that serves precomputed user and item features for real-time personalization models with low latency and high freshness.


## Key Requirements

- Serve features at sub-10ms p99 for online inference in ranking and recommendation
- Support both batch-computed features and near-real-time streaming features
- Maintain point-in-time correctness to prevent training/serving skew


## Core Components

- Offline store: batch feature pipelines write to a columnar store (Parquet, Delta Lake)
- Online store: low-latency key-value store (Redis, DynamoDB) for serving
- Streaming ingestion: Kafka/Flink pipeline for near-real-time feature updates
- Feature registry: metadata catalog with schemas, owners, lineage, and freshness SLAs
- Serving layer: API that joins features from multiple groups into a single vector


## Key Trade-offs

- Precomputed features (fast serving) vs on-demand computation (always fresh)
- Separate offline/online stores (optimized) vs unified store (simpler ops)
- Strict point-in-time joins (correctness) vs relaxed joins (simpler pipelines)


## Must Explain in Interview

- Why training/serving skew happens and how point-in-time joins prevent it
- How you backfill the online store when a new feature is added
- What consistency model you use between batch and streaming feature writes
- How you handle feature freshness SLAs and alert when features go stale
- How the serving layer assembles features from multiple feature groups efficiently
