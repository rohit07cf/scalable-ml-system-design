# Design a Real-Time Recommendation Engine

Design a recommendation engine that adapts to user behavior within the current session, not just historical preferences.


## Key Requirements

- Update recommendations within seconds of new user interactions
- Serve results under 100ms latency at peak traffic
- Blend long-term user preferences with short-term session intent


## Core Components

- Session feature aggregator: streaming pipeline that computes real-time interaction features
- Nearline scoring service: re-ranks candidates using fresh session context without full model retraining
- Precomputed candidate sets: periodically generated offline, filtered and re-scored in real time
- Feature store with dual read paths: batch-updated user profiles and stream-updated session state
- Fallback strategy: graceful degradation to cached or popularity-based results under load


## Key Trade-offs

- Freshness of signals vs infrastructure cost of streaming feature pipelines
- Full real-time model inference vs lightweight re-scoring of precomputed candidates
- Session-level personalization vs risk of overfitting to noisy short-term signals


## Must Explain in Interview

- How you separate the offline candidate generation path from the real-time re-scoring path
- Why streaming feature computation introduces consistency challenges and how you handle late-arriving events
- How to design the feature store so that batch and streaming features are joined correctly at serving time
- What happens when the real-time pipeline is degraded and how fallback logic preserves user experience
- How you evaluate whether real-time signals actually improve recommendations over batch-only baselines
