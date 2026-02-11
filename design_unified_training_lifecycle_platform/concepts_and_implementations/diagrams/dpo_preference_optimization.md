# Diagram: DPO Preference Optimization


## The Core Idea (One Picture)

```
╔══════════════════════════════════════════════════════════════╗
║                     DPO TRAINING                            ║
║                                                              ║
║   PPO does:   prefs → Reward Model → RL loop → better model ║
║   DPO does:   prefs ─────────────────────────→ better model ║
║                          (skip the middlemen)                ║
╚══════════════════════════════════════════════════════════════╝
```


## Full DPO Flow

```
┌──────────────────────────────────────────────────────────┐
│                                                           │
│              PREFERENCE PAIR                              │
│                                                           │
│   Prompt:   "Customer: My order is late."                 │
│   Chosen:   "I'm sorry! Let me track it now."             │
│   Rejected: "Check the website."                          │
│                                                           │
└──────────────────┬───────────────────────────────────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
   ┌─────────────┐   ┌─────────────┐
   │   POLICY    │   │  REFERENCE  │
   │   (LLM)    │   │   (frozen   │
   │  trainable  │   │    copy)    │
   └──────┬──────┘   └──────┬──────┘
          │                 │
          ▼                 ▼
   Compute log probs  Compute log probs
   for BOTH chosen    for BOTH chosen
   and rejected       and rejected
          │                 │
          │    ┌─────────┐  │
          └──> │ DPO     │<─┘
               │ LOSS    │
               │         │
               │ For the policy (vs reference): │
               │                                │
               │ Is the policy's preference     │
               │ for "chosen" over "rejected"   │
               │ STRONGER than the reference's? │
               │                                │
               │ If not → loss is high          │
               │ If yes → loss is low           │
               └────────┬───────────────────────┘
                        │
                        ▼
               Update policy weights
               (make it prefer "chosen" more)
                        │
                        ▼
               ── next preference pair ──
```


## The DPO Loss In Plain English

```
For each preference pair, compute 4 numbers:

  π(chosen)    = policy's log probability of chosen response
  π(rejected)  = policy's log probability of rejected response
  ref(chosen)  = reference's log probability of chosen response
  ref(rejected)= reference's log probability of rejected response

Then:
  policy_gap     = π(chosen) - π(rejected)
  reference_gap  = ref(chosen) - ref(rejected)

  DPO wants:  policy_gap  >>  reference_gap
              ──────────      ─────────────
              "policy should prefer         "relative to how
               chosen over rejected          the reference
               MORE than..."                 sees them"
```

### Why "relative to reference"?

Without the reference anchor, the model might just:
- Make everything more likely (collapse to uniform)
- Or make everything less likely (collapse to silence)

The reference keeps it grounded.

> Think of it like: "improve your preference for the good answer,
> but don't change your overall personality."


## Toy Numeric Example

```
Before training (step 0):
  π(chosen)    = -2.5      ref(chosen)    = -2.5
  π(rejected)  = -2.8      ref(rejected)  = -2.8
  policy_gap   = +0.3      reference_gap  = +0.3

  DPO loss says: "policy_gap == reference_gap → no improvement yet"

After training (step 100):
  π(chosen)    = -1.8      ref(chosen)    = -2.5  (unchanged)
  π(rejected)  = -3.5      ref(rejected)  = -2.8  (unchanged)
  policy_gap   = +1.7      reference_gap  = +0.3

  DPO loss says: "policy_gap >> reference_gap → great! low loss"

What happened:
  ✓ Policy made "chosen" MORE likely     (-2.5 → -1.8)
  ✓ Policy made "rejected" LESS likely   (-2.8 → -3.5)
  ✓ Both relative to the reference anchor
```


## Memory Comparison (Side by Side)

```
              PPO                              DPO
    ┌──────────────────────┐        ┌──────────────────────┐
    │ Policy    (14 GB)    │        │ Policy    (14 GB)    │
    │ Reference (14 GB)    │        │ Reference (14 GB)    │
    │ Reward M. (14 GB)    │        │                      │
    │ Value M.  (14 GB)    │        │                      │
    ├──────────────────────┤        ├──────────────────────┤
    │ Total: ~56 GB        │        │ Total: ~28 GB        │
    │ + optimizer states   │        │ + optimizer states   │
    └──────────────────────┘        └──────────────────────┘

    DPO uses ~HALF the GPU memory of PPO
```


## The Beta (β) Parameter

```
  loss = -log(σ(β × (policy_gap - reference_gap)))

  β controls the "temperature" of the preference:

    β = 0.5  →  aggressive: allow large changes from reference
    β = 0.1  →  conservative: keep close to reference (default)
    β = 0.01 →  very conservative: barely change

  In practice: start with β = 0.1, tune from there.
```

> Think of it like: β is DPO's version of PPO's KL penalty.
> Same job — prevent the model from going off the rails.


## What to Say in Interviews

- "DPO eliminates the reward model and RL loop entirely. It directly
  optimizes the policy using preference pairs — making the model's
  preference for 'chosen' over 'rejected' stronger relative to a
  frozen reference model."

- "It needs only two models in memory instead of four, cutting GPU
  cost roughly in half. The training is standard supervised learning —
  no RL instability, simpler hyperparameters."

- "The main limitation is flexibility: DPO can only learn from pairwise
  preferences. If you need a custom reward signal combining multiple
  objectives, PPO is more appropriate."


## TL;DR (Interview Summary)

- DPO = preference pairs go directly into training — no reward model, no RL loop
- Loss function: "widen policy's chosen-vs-rejected gap relative to reference"
- Only 2 models in memory (policy + reference) — half the GPU cost of PPO
- Beta parameter controls conservatism (how far model can deviate)
- Standard supervised training — stable, simple, fewer hyperparameters
- Reference model prevents collapse — keeps the model grounded
- Limitation: only works with pairwise preferences, not arbitrary reward signals
