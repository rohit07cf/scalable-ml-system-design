# Design: Serverless Inference

Design an inference system using serverless compute that scales to zero during idle periods and handles unpredictable, bursty traffic.


## Key Requirements

- Scale from zero to thousands of concurrent requests within seconds
- Keep cost near zero during idle periods (pay-per-invocation model)
- Meet P95 latency targets despite cold start overhead


## Core Components

- Serverless function layer (Lambda, Cloud Run, or Knative) with container image packaging
- Model artifact loading strategy: pre-baked in image vs fetched from object storage on cold start
- Warm pool manager with provisioned concurrency for latency-sensitive paths
- Request queue with backpressure to absorb burst traffic beyond scaling speed
- Lightweight model registry mapping routes to versioned model artifacts and configs


## Key Trade-offs

- Scale-to-zero saves cost but cold starts add 1-10s latency depending on model size
- Pre-baked model images start faster but increase image size and deployment time
- Provisioned concurrency reduces cold starts but reintroduces fixed cost (partial scale-to-zero)


## Must Explain in Interview

- Cold start anatomy: container init, runtime init, model load -- and which phase dominates for ML
- When serverless makes sense: low/bursty QPS, cost sensitivity, models under ~500MB
- Warm pool sizing: how to estimate provisioned concurrency from traffic patterns
- Comparison with dedicated GPU serving: break-even QPS where serverless becomes more expensive
- Model packaging strategies: layer caching, EFS mounts, and snapshot-based fast restore
