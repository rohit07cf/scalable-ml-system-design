# Design a Personalized Feed Ranking System

Design a ranking system that orders a heterogeneous content feed (posts, ads, stories) for each user in real time.


## Key Requirements

- Rank mixed content types (organic, sponsored, social) under a unified scoring framework
- Incorporate real-time engagement signals within the current session
- Support multiple business objectives simultaneously (engagement, revenue, content quality)


## Core Components

- Pointwise ranking model predicting per-item engagement probabilities (click, like, share, hide)
- Multi-objective scoring function combining weighted predictions into a single rank score
- Feature engineering layer: user profile, item metadata, cross features, real-time context
- Online feature serving with low-latency access to historical and session-level features
- A/B testing framework to measure ranking changes against long-term user health metrics


## Key Trade-offs

- Multi-objective weighting: engagement vs revenue vs user satisfaction
- Model complexity (deep ranking models) vs serving latency at request time
- Global ranking fairness vs per-user personalization depth


## Must Explain in Interview

- How to combine multiple prediction heads (P(click), P(share), P(hide)) into one ranking score
- Why you need both user-level and session-level features and how staleness affects each
- How to detect and mitigate feedback loops where the model only learns to rank what it already shows
- What calibration means for ranking models and why raw logits are not directly comparable across content types
- How you would run an A/B test that measures long-term retention, not just short-term engagement lift
