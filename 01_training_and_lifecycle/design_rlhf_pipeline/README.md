# Design: RLHF / Alignment Training Pipeline

Design a pipeline that collects human preference data, trains a reward model, and aligns an LLM using reinforcement learning from human feedback.


## Key Requirements

- Collect, validate, and version pairwise human preference labels at scale (10K-500K comparisons)
- Train and evaluate a reward model that reliably scores response quality
- Run PPO or DPO alignment training with stability controls, then validate before deployment


## Core Components

- Annotation platform -- serves prompt-response pairs to labelers, enforces quality (agreement checks, honeypots)
- Preference dataset store -- versions labeled data with annotator metadata, inter-rater agreement scores
- Reward model trainer -- fine-tunes a classifier on preference pairs, evaluates ranking accuracy and calibration
- Alignment trainer -- runs PPO (reward + value + reference model) or DPO (simpler, reference + policy only)
- Safety evaluator -- tests aligned model for refusal accuracy, jailbreak resistance, and helpfulness regression


## Key Trade-Offs

- PPO vs DPO: PPO is more expressive but requires 4 models in memory and is unstable; DPO is simpler and often sufficient
- Human labels vs AI labels (RLAIF): cost and speed vs label quality; most production systems blend both
- Strong alignment vs helpfulness: over-optimizing the reward model causes refusal of benign queries


## Must Explain in Interview

- The 3-phase RLHF loop: SFT baseline, reward model training, RL fine-tuning
- Why a reference model is needed: KL penalty prevents the policy from diverging too far and reward hacking
- Reward model failure modes: over-optimization (Goodhart's Law), length bias, sycophancy
- DPO's key insight: reparameterize the reward into a closed-form loss, eliminating the RL loop entirely
- Label quality levers: annotator guidelines, inter-rater agreement thresholds, consensus labeling, and calibration sets
