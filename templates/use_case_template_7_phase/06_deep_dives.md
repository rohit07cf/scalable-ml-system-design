# Phase 6 -- Deep Dives


## Scaling

- Describe horizontal scaling strategy for the serving layer
- Explain how training scales with data size (distributed training, data parallelism)
- Address auto-scaling triggers and cooldown policies


## Reliability

- Identify single points of failure and how to eliminate them
- Describe retry, circuit breaker, and fallback strategies
- Explain model rollback procedure if a bad model is deployed


## Performance

- Describe caching strategy (what to cache, TTL, invalidation)
- Explain batching and prefetching optimizations for inference
- Note model optimization techniques (quantization, distillation, pruning)


## Security

- Describe how PII and sensitive data are handled in training and serving
- Note input validation and adversarial input protection
- Address model access control and audit logging
