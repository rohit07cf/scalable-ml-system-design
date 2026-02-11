# Design a Bandit-Based Exploration System

Design an exploration system that balances exploiting known-good recommendations with exploring uncertain or new content.


## Key Requirements

- Allocate a controlled fraction of traffic to exploration without degrading overall user experience
- Accelerate learning for cold-start items that lack engagement data
- Provide measurable improvement in catalog coverage and long-tail discovery


## Core Components

- Contextual bandit policy: selects actions (items to show) conditioned on user and context features
- Reward modeling: maps observed signals (click, watch time, skip) to a scalar reward for policy updates
- Exploration budget controller: limits the fraction of impressions allocated to exploratory items
- Logging policy tracker: records which policy served each impression for unbiased offline evaluation
- Cold-start item pool: prioritizes newly added or under-exposed items for exploration slots


## Key Trade-offs

- Epsilon-greedy (simple, uniform exploration) vs Thompson sampling (adaptive, higher variance)
- Aggressive exploration (faster learning) vs conservative exploration (lower short-term engagement cost)
- Online policy updates (fresh, operationally complex) vs periodic batch retraining (simpler, slower to adapt)


## Must Explain in Interview

- Why naive A/B testing of new items is insufficient and how bandits reduce the cost of exploration
- How inverse propensity scoring corrects for logging policy bias in offline evaluation
- What the difference is between context-free bandits and contextual bandits and when each applies
- How you set and adapt the exploration budget without manual tuning
- Why ignoring exploration leads to popularity bias and catalog stagnation over time
