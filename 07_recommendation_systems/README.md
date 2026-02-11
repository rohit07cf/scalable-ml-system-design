# Recommendation Systems

## What This Section Covers

- Multi-stage recommendation pipelines: candidate generation, scoring, reranking
- Embedding-based retrieval and two-tower architectures for large item catalogs
- Real-time feature serving and online learning for personalization
- Exploration-exploitation trade-offs using bandit and contextual bandit methods

## What Interviewers Usually Test

- Can you design a full retrieval-to-ranking pipeline that scales to millions of items?
- Do you understand how to balance relevance, diversity, and freshness in ranked outputs?
- Can you reason about cold-start, feedback loops, and exploration strategies?

## Suggested Study Order

1. `design_video_recommendation_system` -- end-to-end multi-stage pipeline
2. `design_personalized_feed_ranking` -- ranking model design and feature engineering
3. `design_real_time_recommendation_engine` -- online signals and low-latency serving
4. `design_two_tower_embedding_system` -- scalable candidate generation with embeddings
5. `design_bandit_exploration_system` -- exploration strategies and cold-start handling

## Fast Revision Path

- Review core components and trade-offs in each design README
- Focus on the "must explain in interview" bullets across all five designs
- Sketch one end-to-end diagram covering: candidate generation -> scoring -> reranking -> serving
