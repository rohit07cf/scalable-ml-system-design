# 07 — DPO Explained with Toy Example


## Setup: Same Customer Support Model

We have the same fine-tuned model and preference data.

But this time: **no reward model, no RL loop**.

DPO directly trains the model to prefer chosen responses over rejected ones.


## Key Insight: Why DPO Works

The DPO paper showed that you can skip the reward model entirely.

Instead of:
```
preference data → train RM → RL loop with RM → better model
```

DPO does:
```
preference data → one training step → better model
```

> Think of it like: PPO hires a judge (RM), then trains the student
> (LLM) to impress the judge. DPO skips the judge and teaches the
> student directly from the answer key (preference pairs).


## How DPO Works (Step by Step)

### What you need

1. A fine-tuned LLM (the "policy" you want to improve)
2. A frozen copy of that same LLM (the "reference")
3. Preference data: (prompt, chosen, rejected) triplets

### The training step

For each preference pair:

```
1. Feed "prompt + chosen" through BOTH policy and reference model
   → get log probability of "chosen" from each

2. Feed "prompt + rejected" through BOTH policy and reference model
   → get log probability of "rejected" from each

3. Compute the DPO loss:
   "Make the policy relatively more likely to produce 'chosen'
    and relatively less likely to produce 'rejected'
    compared to the reference model"

4. Update only the policy weights (reference stays frozen)
```


### In plain English

The loss says:

> "Increase the gap between how much the policy prefers 'chosen'
> over 'rejected', relative to how the reference model saw them."

The "relative to reference" part is important — it prevents the model
from just making everything more likely (or less likely).


### Tiny walkthrough

```
Prompt: "Customer: My order is late."

Chosen:   "I'm so sorry! Let me track your order right now."
Rejected: "Check the website."

Step 1:
  policy_log_prob(chosen)    = -2.1    (policy thinks chosen is likely)
  reference_log_prob(chosen) = -3.0    (reference thinks chosen is less likely)

  policy_log_prob(rejected)    = -4.5  (policy thinks rejected is unlikely)
  reference_log_prob(rejected) = -3.2  (reference thought rejected was more likely)

Step 2:
  policy "margin" for chosen vs rejected:
    chosen_diff  = policy(chosen) - ref(chosen)     = -2.1 - (-3.0) = +0.9
    rejected_diff = policy(rejected) - ref(rejected) = -4.5 - (-3.2) = -1.3

  DPO wants: chosen_diff >> rejected_diff  ✓ (0.9 >> -1.3, good!)

Step 3:
  Loss pushes the policy to widen this gap further.
```


## ASCII Diagram

```
┌───────────────────────────────────────────────────┐
│                 DPO TRAINING                      │
│                                                   │
│  ┌───────────────────────┐                        │
│  │   Preference Pair      │                        │
│  │   prompt + chosen      │                        │
│  │   prompt + rejected    │                        │
│  └───────────┬────────────┘                        │
│              │                                    │
│       ┌──────┴──────┐                              │
│       ▼              ▼                              │
│  ┌─────────┐   ┌──────────┐                        │
│  │ Policy  │   │Reference │                        │
│  │  (LLM)  │   │  (frozen │                        │
│  │trainable│   │  copy)   │                        │
│  └────┬────┘   └────┬─────┘                        │
│       │              │                              │
│       ▼              ▼                              │
│  log probs      log probs                          │
│  of chosen &    of chosen &                        │
│  rejected       rejected                           │
│       │              │                              │
│       └──────┬───────┘                              │
│              ▼                                      │
│     ┌─────────────────┐                            │
│     │   DPO Loss       │                            │
│     │                  │                            │
│     │ "Widen the gap   │                            │
│     │  between chosen  │                            │
│     │  and rejected    │                            │
│     │  relative to     │                            │
│     │  reference"      │                            │
│     └────────┬─────────┘                            │
│              │                                      │
│              ▼                                      │
│     Update policy weights                          │
│     (reference stays frozen)                       │
└───────────────────────────────────────────────────┘
```


## Why DPO Is Simpler Than PPO

| | PPO | DPO |
|---|---|---|
| **Models needed** | 4 (policy, ref, RM, value) | 2 (policy, ref) |
| **Training steps** | RM training + RL loop | One supervised training pass |
| **Hyperparameters** | Many (KL coef, clip, LR, RM training...) | Few (beta, LR) |
| **Stability** | Can be unstable, reward hacking | Stable, standard loss function |
| **GPU memory (7B)** | ~56 GB (4 models) | ~28 GB (2 models) |
| **Implementation** | Custom RL code | Standard HF Trainer |


## When DPO Works Well

- You have **clean, high-quality preference data**
- Alignment goal is straightforward (helpful, harmless, polite)
- Budget is limited
- You want **fast iteration** (no RM training overhead)
- Most practical enterprise alignment tasks

## Limitations of DPO

- Can't express rewards beyond pairwise preferences
  - PPO can use any scalar reward (e.g., factuality score + safety score combined)

- Quality is bounded by preference data quality
  - Bad labels → bad alignment (no RM to "generalize" beyond labels)

- Less exploration than PPO
  - PPO generates new responses and explores; DPO only learns from existing pairs

- If preferences are **very noisy or contradictory**, PPO with a good RM may handle it better
  - The RM can smooth out noise; DPO takes labels at face value


## The Beta Parameter

DPO has one key hyperparameter: **beta (β)**

- Controls how much the model can deviate from the reference
- **Higher beta** → stay closer to reference (conservative, stable)
- **Lower beta** → allow more change (aggressive, may overfit)

Typical values: β = 0.1 to 0.5

> Think of it like: beta is the DPO equivalent of PPO's KL penalty.
> Same purpose — don't let the model wander too far.


## Common Mistakes

- Using low-quality preference data and expecting good results
  — DPO has no RM to "generalize" — it trusts the labels directly

- Setting beta too low → model overfits to preference patterns

- Forgetting to freeze the reference model → no stable anchor

- Thinking DPO can't do what PPO does
  — for most practical tasks, it can; PPO's edge is in complex reward signals


## What to Say in Interviews

> "DPO skips the reward model entirely. It takes preference pairs —
> chosen and rejected responses — and directly trains the model to
> increase the probability gap between chosen and rejected, relative
> to a frozen reference. This needs only two models in memory instead
> of four, making it roughly half the cost of PPO. For most alignment
> tasks with clean preference data, DPO matches PPO quality with
> simpler implementation and faster training."

### Follow-up: "When would you use PPO instead?"

> "When the reward signal can't be expressed as simple pairwise
> preferences — for example, combining a factuality score, a safety
> score, and a helpfulness score into one reward. PPO can optimize
> against any scalar reward function; DPO is limited to preference
> pairs."


## TL;DR (Interview Summary)

- DPO trains directly on preference pairs — no reward model needed
- Only 2 models in memory (policy + reference) vs PPO's 4 — half the GPU cost
- Loss function: "widen the gap between chosen and rejected relative to reference"
- Beta parameter controls how far the model can deviate (like PPO's KL penalty)
- Simpler, more stable, fewer hyperparameters than PPO
- Works best with clean preference data and straightforward alignment goals
- Limitation: can't handle complex multi-objective reward signals (PPO can)
- Default choice for most enterprise alignment — only escalate to PPO if needed
