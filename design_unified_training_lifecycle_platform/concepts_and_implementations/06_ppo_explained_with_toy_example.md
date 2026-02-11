# 06 — PPO Explained with Toy Example


## Setup: Customer Support Reply Model

We have a fine-tuned model that writes support replies.
Now we want to make it prefer replies that humans rate highly.

**We already have:**
- A fine-tuned LLM (the "policy" — the model we're improving)
- Preference data (used to train a reward model)

**We need to build:**
- A reward model that scores any (prompt, reply) pair
- A PPO training loop that makes the LLM chase higher scores


## Key Terms (One Line Each)

- **Policy** = the LLM we're training (it "decides" what to output)
- **Reward Model (RM)** = a separate model that scores outputs (higher = better)
- **Reference Model** = a frozen copy of the policy before PPO starts
- **Value Model** = estimates expected future reward (helps stabilize training)
- **Advantage** = "was this output better or worse than expected?"
- **KL Penalty** = keeps the policy from drifting too far from the reference


## The PPO Loop (Step by Step)

### Step 0: Train the Reward Model (one-time)

```
Input:  preference pairs (prompt, chosen, rejected)
Output: a model that scores (prompt, response) → scalar score

Training:
  For each pair:
    score_chosen  = RM(prompt, chosen)
    score_rejected = RM(prompt, rejected)
    loss = -log(sigmoid(score_chosen - score_rejected))
    → push chosen scores UP, rejected scores DOWN
```

### Steps 1–4: PPO Training Loop (repeated)

```
┌──────────────────────────────────────────────────────────┐
│                    PPO TRAINING LOOP                     │
│                                                          │
│  ┌──────────┐    generate    ┌──────────────────┐        │
│  │  Prompt   │ ──────────> │  Policy (LLM)     │        │
│  │  batch    │              │  generates reply   │        │
│  └──────────┘              └────────┬───────────┘        │
│                                     │                    │
│                                     ▼                    │
│                            ┌──────────────────┐          │
│                            │  Reward Model    │          │
│                            │  scores reply    │          │
│                            │  → score = 0.82  │          │
│                            └────────┬─────────┘          │
│                                     │                    │
│                                     ▼                    │
│                            ┌──────────────────┐          │
│                            │  Compute          │          │
│                            │  Advantage        │          │
│                            │  = reward - value │          │
│                            │  (was it better   │          │
│                            │   than expected?) │          │
│                            └────────┬─────────┘          │
│                                     │                    │
│                                     ▼                    │
│                            ┌──────────────────┐          │
│                            │  PPO Update       │          │
│                            │  + KL penalty     │          │
│                            │  (don't drift     │          │
│                            │   too far from    │          │
│                            │   reference)      │          │
│                            └────────┬─────────┘          │
│                                     │                    │
│                                     ▼                    │
│                            Policy weights updated        │
│                            → repeat with next batch      │
└──────────────────────────────────────────────────────────┘
```

### Step 1: Generate responses

```
Prompt: "Customer: My order arrived damaged."
Policy generates: "I'm so sorry about that! Let me arrange
  a replacement immediately and send you a prepaid return label."
```

### Step 2: Score with Reward Model

```
RM(prompt, response) → 0.82  (high score = good reply)
```

The RM learned from preference data what "good" looks like.

### Step 3: Compute advantage

```
advantage = reward - value_estimate
          = 0.82  - 0.65
          = +0.17  (better than expected → reinforce this behavior)
```

- Positive advantage → make this output more likely
- Negative advantage → make this output less likely

### Step 4: PPO update

```
Update policy to increase probability of high-advantage outputs.

BUT — add a KL penalty:
  kl_penalty = KL(policy || reference_model)
  If the policy drifts too far from the original → penalty kicks in

final_reward = reward - beta * kl_penalty

PPO also clips the update size:
  "Don't change the probabilities by more than epsilon (e.g., 0.2)"
```

> Think of it like: the KL penalty is a leash.
> The model can explore better responses, but it can't wander
> so far that it forgets how to speak coherently.


## Why "Keep Changes Small"? (The PPO Constraint)

Without constraints, the model would:
- Find weird outputs that "hack" the reward model for high scores
- But sound nonsensical to humans

PPO prevents this two ways:
1. **KL penalty** — punishes divergence from the reference model
2. **Clipping** — caps how much any single update can change probabilities

This is the core insight of PPO: improve, but cautiously.


## The Four Models in Memory

| Model | Size | Role | Trainable? |
|---|---|---|---|
| **Policy** | Full model | Generates responses | Yes |
| **Reference** | Full model | KL penalty anchor | No (frozen) |
| **Reward Model** | Full model | Scores outputs | No (frozen) |
| **Value Model** | Full model (or smaller) | Estimates expected reward | Yes |

Total memory: ~4x model size (this is why PPO is expensive).

For a 7B model: ~4 × 14 GB ≈ 56 GB minimum.


## Common Mistakes

- Forgetting the KL penalty → model "reward hacks" (high RM score, gibberish text)

- Reward model too simple → doesn't capture real preferences well

- Training too long → model becomes repetitive (exploits RM patterns)

- Not freezing the reference model → no anchor for KL penalty

- Confusing "reward model" with "the model we're training"
  — RM is a separate scorer; policy is the LLM being improved


## What to Say in Interviews

> "PPO works in a loop: the policy generates responses, a reward model
> scores them, and PPO updates the policy to increase the probability
> of high-scoring outputs. The key constraint is a KL penalty that
> prevents the model from drifting too far from the original, which
> stops reward hacking. The downside is cost — you need four models
> in memory: the policy, a frozen reference, the reward model, and
> a value model."

### Follow-up: "Why not just maximize the reward?"

> "Without the KL constraint, the model finds adversarial outputs
> that exploit quirks in the reward model — high scores but nonsensical
> text. The KL penalty anchors the policy to the reference so it stays
> coherent."


## TL;DR (Interview Summary)

- PPO loop: generate → score with RM → compute advantage → update policy
- Reward model trained separately on preference data (chosen vs rejected)
- KL penalty prevents policy from drifting too far from reference (stops reward hacking)
- PPO clipping caps update size — "improve, but cautiously"
- 4 models in memory: policy, reference, RM, value model (~4x model size)
- Advantage = reward - expected_value ("was this better than expected?")
- Main risk: reward hacking (model games the RM for high scores)
- PPO is powerful but expensive — DPO is the simpler/cheaper alternative
