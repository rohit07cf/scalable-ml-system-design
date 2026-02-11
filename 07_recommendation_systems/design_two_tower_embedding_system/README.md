# Design a Two-Tower Embedding System

Design an embedding-based retrieval system that encodes users and items into a shared vector space for fast candidate generation.


## Key Requirements

- Retrieve top-k candidates from hundreds of millions of items in single-digit milliseconds
- Support frequent item index updates as new content is added
- Maintain embedding quality as user preferences and item distributions shift over time


## Core Components

- User tower: encodes user features and history into a dense embedding at query time
- Item tower: encodes item features into dense embeddings, precomputed and indexed offline
- Approximate nearest neighbor index (HNSW, ScaNN) for sub-linear retrieval over item embeddings
- Training pipeline: contrastive or softmax loss over positive interactions with hard negative mining
- Index refresh pipeline: periodic re-embedding and re-indexing as the item catalog changes


## Key Trade-offs

- In-batch negatives (cheap, biased toward popular items) vs hard negatives (expensive, better quality)
- Embedding dimensionality: higher recall vs increased storage and retrieval latency
- Frequent index rebuilds (fresh) vs incremental updates (faster but risk index drift)


## Must Explain in Interview

- Why the two towers are decoupled at serving time and what this enables for latency
- How the choice of negative sampling strategy directly affects what the model learns to retrieve
- Why inner product and cosine similarity behave differently and when each is appropriate
- How you detect embedding drift over time and decide when to retrain
- What the failure modes are when the ANN index returns stale or poorly distributed candidates
