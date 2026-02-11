# 05 — RLHF Basics


## Why Does RLHF Exist?

Fine-tuning teaches a model **what** to say (task format, style, knowledge).

But it doesn't teach the model **which** answer humans actually prefer.

- Two replies can both be grammatically correct and on-topic
- But one is clearly better (more helpful, safer, more natural)
- Fine-tuning alone can't distinguish "good" from "great"

**RLHF** = Reinforcement Learning from Human Feedback

- Collect human preferences: "Response A is better than Response B"
- Use those preferences to steer the model toward preferred outputs

> Think of it like: fine-tuning teaches the model to speak your language.
> RLHF teaches it to say the things humans actually want to hear.


### Customer Support Example

After fine-tuning, the model generates two candidate replies:

| | Reply |
|---|---|
| **A** | "I apologize for the issue. Let me escalate this to our team and we'll have a resolution for you by end of day." |
| **B** | "Sorry about that. Someone will look into it." |

Both are polite. Both are on-topic. But humans consistently prefer **A**.

RLHF trains the model to produce more A-like responses.


## What Is Preference Data?

The raw material for RLHF. Each example is a triplet:

```json
{
  "prompt":   "Customer: My order is wrong. What should I do?",
  "chosen":   "I'm so sorry! Let me fix this right away...",
  "rejected": "Contact support."
}
```

- **prompt** — the input
- **chosen** — the response a human preferred
- **rejected** — the response a human did NOT prefer

You need hundreds to thousands of these pairs.

More details on collection in `08_preference_data_pipeline.md`.


## The Three RLHF Approaches (High Level)

### 1. Classic RLHF with Reward Model + PPO

```
Step 1: Train a Reward Model (RM)
        Input: (prompt, response) → Output: score (0–1)
        Trained on preference data to predict which response humans prefer

Step 2: Use RM to train the LLM via PPO (Reinforcement Learning)
        LLM generates response → RM scores it → PPO updates LLM to get higher scores
```

- More complex (4 models in memory)
- More flexible (any reward signal)
- Details in `06_ppo_explained_with_toy_example.md`

### 2. DPO (Direct Preference Optimization)

```
Skip the reward model entirely.
Directly train the LLM on preference pairs.
Loss function makes the model prefer "chosen" over "rejected".
```

- Simpler (2 models in memory)
- Cheaper and more stable
- Details in `07_dpo_explained_with_toy_example.md`

### 3. RLHF with AI Feedback (RLAIF)

- Same as #1 or #2, but preferences come from another AI (e.g., GPT-4)
- Cheaper than human labeling
- Quality depends on the AI judge
- Good for bootstrapping, then refine with human labels


## PPO vs DPO: When to Choose

| | PPO | DPO |
|---|---|---|
| **Complexity** | High (4 models) | Low (2 models) |
| **GPU cost** | ~2–3x more | Baseline |
| **Stability** | Harder to tune | Stable |
| **Reward signal** | Any (can be multi-objective) | Only preference pairs |
| **Quality** | Slightly higher ceiling | Very close in practice |
| **When to use** | Complex alignment, custom rewards | Clean preference data, most use cases |

### If you forget everything else:

> **Start with DPO.** It's simpler, cheaper, and works well for most
> alignment tasks. Only move to PPO if you need a custom reward signal
> that can't be expressed as preference pairs.


## How RLHF Fits in the Training Lifecycle

```
1. Pretrain         →  base LLM (knows language)
2. Fine-tune (SFT)  →  task-adapted LLM (knows your format/domain)
3. RLHF (PPO/DPO)   →  aligned LLM (outputs match human preferences)
```

- RLHF is usually the **last** training step
- It starts from a fine-tuned model, not from a base model
- The input is always: fine-tuned model + preference data


## Common Mistakes

- Skipping SFT and going straight to RLHF
  — the model needs to know the task format first

- Thinking RLHF replaces fine-tuning
  — it doesn't; it's an additional alignment step on top

- Using noisy/low-quality preference data
  — garbage preferences = garbage alignment

- Thinking PPO is always better than DPO
  — DPO matches PPO quality in most practical settings


## Interview Answer: "What is RLHF?"

> "RLHF uses human preference data — where annotators pick which of two
> model responses is better — to align the model's outputs with what
> humans actually prefer. The classic approach trains a reward model on
> preferences, then uses PPO to optimize the LLM against that reward.
> DPO is a simpler alternative that skips the reward model and directly
> trains on preference pairs. For most use cases, DPO is the practical
> starting point because it's cheaper and more stable."


## TL;DR (Interview Summary)

- RLHF = align model outputs with human preferences (beyond just task accuracy)
- Preference data = (prompt, chosen_response, rejected_response) triplets
- Classic RLHF: train a reward model, then optimize LLM via PPO (complex, flexible)
- DPO: skip reward model, train directly on preferences (simpler, cheaper, stable)
- RLHF comes AFTER fine-tuning — it's the alignment layer, not a replacement
- Start with DPO unless you need a custom/multi-objective reward signal
- Quality of preference data is the #1 factor in RLHF success
- RLAIF (AI feedback) can bootstrap preferences cheaply, refine with humans later
