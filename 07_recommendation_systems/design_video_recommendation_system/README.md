# Design a Video Recommendation System

Design a system that recommends relevant videos to hundreds of millions of users from a catalog of billions of items.


## Key Requirements

- Serve personalized recommendations at scale with sub-200ms latency
- Handle a catalog of billions of videos with continuous new uploads
- Optimize for long-term engagement, not just click-through rate


## Core Components

- Candidate generation layer: retrieve hundreds from billions using lightweight models
- Ranking model: score candidates using dense user and item features
- Reranking layer: enforce diversity, freshness, and business rules post-scoring
- Feature store: serve precomputed user history and real-time session signals
- Feedback pipeline: log impressions, clicks, watch time; close the training loop


## Key Trade-offs

- Optimizing watch time vs promoting content diversity and discovery
- Precomputed recommendations (fast, stale) vs real-time scoring (fresh, expensive)
- Simple two-stage pipeline vs multi-stage cascade with increasing model complexity


## Must Explain in Interview

- Why candidate generation and ranking are separate stages and what each optimizes for
- How negative sampling works in implicit feedback settings (watched vs not-shown is not the same as disliked)
- Why position bias in training data degrades ranking quality and how to correct for it
- How you handle new videos with no engagement signal (cold-start at the item level)
- What metrics you track online (watch time, session length, next-day retention) and why CTR alone is insufficient
