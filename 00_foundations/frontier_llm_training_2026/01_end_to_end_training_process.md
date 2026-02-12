# 01 — End-to-End Training Process


## The Three Phases

Frontier model training has three distinct phases, executed in sequence:

1. **Pre-training** — learn language from raw text (self-supervised)
2. **Supervised fine-tuning (SFT)** — learn to follow instructions
3. **Alignment** — learn human preferences (RLHF, DPO, etc.)

Each phase has different data, objectives, compute requirements, and duration.


## Phase 1: Pre-Training

**Objective**: Next-token prediction on massive text corpora.

- **Self-supervised** — no human labels needed
- Model learns grammar, facts, reasoning patterns, code, math
- Trained on **trillions of tokens** (5T–20T+ as of early 2026)
- Data: web crawl, books, code, scientific papers, multilingual text
- Loss function: cross-entropy on next-token prediction

**This is the most expensive phase by far.**

| Aspect | Typical Range |
|---|---|
| Duration | 2–6 months of continuous training |
| Compute | 10K–100K+ GPUs running 24/7 |
| Cost | $50M–$500M+ (depends on scale) |
| Data | 5T–20T+ tokens |
| Output | Base model (strong but not instruction-following) |


## Phase 2: Supervised Fine-Tuning (SFT)

**Objective**: Teach the base model to follow instructions and produce structured outputs.

- Uses (instruction, response) pairs curated by humans or generated synthetically
- Much smaller dataset than pre-training (100K–10M examples)
- Much cheaper and faster than pre-training

| Aspect | Typical Range |
|---|---|
| Duration | Days to 1–2 weeks |
| Compute | Hundreds to low thousands of GPUs |
| Cost | $100K–$5M |
| Data | 100K–10M instruction-response pairs |
| Output | Instruction-following model |


## Phase 3: Alignment (Post-Training)

**Objective**: Steer the model toward outputs humans actually prefer — helpful, harmless, honest.

Multiple techniques, often combined:

### RLHF (Reinforcement Learning from Human Feedback)
- Train a **reward model** on human preference data
- Use PPO to optimize the LLM against the reward model
- Complex (4 models in memory), but powerful
- Used by OpenAI, Anthropic, and others since 2022

### DPO (Direct Preference Optimization)
- Skip the reward model entirely
- Train directly on (chosen, rejected) preference pairs
- Simpler, cheaper, more stable than RLHF
- Widely adopted by early 2026

### ORPO (Odds Ratio Preference Optimization)
- Combines SFT and preference alignment in one training step
- Eliminates the need for a separate SFT phase before alignment
- Newer approach, gaining traction

### KTO (Kahneman-Tversky Optimization)
- Works with binary feedback (good/bad) instead of pairwise preferences
- Easier to collect data — don't need side-by-side comparisons
- Based on prospect theory loss functions

### Synthetic Data Loops
- Use a strong model to generate training data for a weaker model
- **Reasoning distillation**: strong model produces chain-of-thought traces,
  weaker model learns to replicate the reasoning pattern
- Used extensively for reasoning-focused models (o-series, Claude reasoning)
- Increasingly important in early 2026

| Technique | Reward Model? | Data Format | Complexity | Adoption (2026) |
|---|---|---|---|---|
| RLHF (PPO) | Yes | Preference pairs | High | Established |
| DPO | No | Preference pairs | Low | Widespread |
| ORPO | No | Preference pairs | Low | Growing |
| KTO | No | Binary labels | Low | Growing |
| Reasoning distillation | No | Synthetic traces | Medium | Widespread |


## End-to-End Pipeline (Numbered Steps)

```
1. Data collection
   - Web crawl, books, code, licensed data, synthetic data
   - Dedup, filter, quality score, tokenize

2. Pre-training
   - Next-token prediction on trillions of tokens
   - Months of continuous GPU training
   - Periodic checkpoints (every few minutes)

3. Supervised fine-tuning (SFT)
   - Instruction-response pairs (human + synthetic)
   - Days to weeks

4. Alignment
   - RLHF or DPO on human preference data
   - Synthetic data loops for reasoning
   - Days to weeks

5. Safety evaluation
   - Red-teaming, benchmark suites, bias testing
   - Automated + human evaluation

6. Deployment preparation
   - Quantization (for inference efficiency)
   - Distillation (smaller serving models)
   - A/B testing, canary rollout
```


## Pre-Training vs Fine-Tuning vs Alignment

| | Pre-Training | Fine-Tuning (SFT) | Alignment |
|---|---|---|---|
| **Goal** | Learn language | Follow instructions | Match human preferences |
| **Supervision** | Self-supervised | Supervised | Preference-based |
| **Data size** | Trillions of tokens | Millions of examples | Millions of pairs |
| **Duration** | Months | Days–weeks | Days–weeks |
| **Cost** | $50M–$500M+ | $100K–$5M | $100K–$10M |
| **Output** | Base model | Instruction model | Aligned model |
| **Compute** | 10K–100K+ GPUs | 100–1K GPUs | 100–1K GPUs |


## Interview Phrasing

> "Frontier training is a three-phase pipeline. Pre-training is self-supervised
> next-token prediction on trillions of tokens — that's the expensive part,
> running for months on tens of thousands of GPUs. Then SFT teaches the model
> to follow instructions using curated examples. Finally, alignment uses
> techniques like RLHF or DPO to steer outputs toward human preferences.
> In 2026, DPO has largely replaced PPO for alignment because it's simpler
> and cheaper, and synthetic data loops — especially reasoning distillation —
> have become a critical part of post-training."

> "The key insight is that pre-training is 90%+ of the compute cost.
> Post-training (SFT + alignment) is comparatively cheap but has outsized
> impact on model quality and safety."


## TL;DR (Interview Summary)

- Three phases: pre-training (months, $50M–$500M+) -> SFT (days) -> alignment (days)
- Pre-training = self-supervised next-token prediction on trillions of tokens
- SFT = teach instruction-following with curated examples
- Alignment = RLHF, DPO, ORPO, KTO — steer toward human preferences
- DPO has largely displaced PPO by 2026 (simpler, cheaper, similar quality)
- Synthetic data loops and reasoning distillation are now critical post-training steps
- Pre-training is 90%+ of compute cost; post-training is cheap but high-impact
- Know all three phases and be able to explain the tradeoffs between alignment techniques
