# Cost and Latency Checklist

Key cost and latency considerations to address in ML system design interviews.


## Compute Costs

- [ ] GPU vs. CPU inference cost per request for the chosen model size
- [ ] Training cost per run and expected retraining frequency
- [ ] Preprocessing and feature engineering compute overhead
- [ ] Cost of redundant compute for high-availability deployments


## Storage Costs

- [ ] Raw data storage and retention policy (hot vs. cold tiers)
- [ ] Embedding and feature store storage at scale
- [ ] Model artifact storage and versioning overhead
- [ ] Log and audit trail storage for compliance


## Latency Targets

- [ ] End-to-end p50 and p99 latency targets for the serving path
- [ ] Feature retrieval latency from the feature store
- [ ] Model inference latency per request (single model or ensemble)
- [ ] Network latency between services in the critical path


## Optimization Levers

- [ ] Model quantization or distillation to reduce inference cost and latency
- [ ] Caching predictions or embeddings for repeated or similar queries
- [ ] Batching inference requests to improve GPU utilization
- [ ] Precomputation of expensive features or rankings during off-peak hours
