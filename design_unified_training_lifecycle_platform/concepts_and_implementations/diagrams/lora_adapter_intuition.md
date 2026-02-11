# Diagram: LoRA Adapter Intuition


## The Core Idea

A pretrained weight matrix W is huge (e.g., 4096 x 4096).

LoRA says: **don't update W. Instead, add a small correction.**

The correction is a **low-rank** product of two small matrices A and B.


## ASCII Diagram

```
                   ORIGINAL (no LoRA)
                   ──────────────────

        input x                     output
       [4096] ──────> W [4096×4096] ──────> y = W·x



                   WITH LoRA
                   ─────────

        input x
       [4096] ──┬──────────────────────────────┐
                │                               │
                ▼                               ▼
         W [4096×4096]                   A [4096×r]
         (FROZEN)                        (trainable)
                │                               │
                │                               ▼
                │                        B [r×4096]
                │                        (trainable)
                │                               │
                ▼                               ▼
            W·x (original)              A·B·x (correction)
                │                               │
                └──────────── + ────────────────┘
                              │
                              ▼
                    y = W·x + (A·B)·x * scaling
                        ↑          ↑
                    original    LoRA delta
                    (frozen)    (tiny, trained)
```


## Why "Low-Rank"?

- **Rank** (r) is the bottleneck dimension — typically 8 or 16
- A is [4096 × 8], B is [8 × 4096]
- Together: 4096×8 + 8×4096 = **65,536 parameters**
- Original W: 4096×4096 = **16,777,216 parameters**
- **LoRA is ~0.4% the size of W**

> Think of it like: instead of rewriting a 4096-page book,
> you write an 8-page summary of changes.


## Parameter Count Example (7B model)

```
Full model:           7,000,000,000 params
LoRA adapters (r=8):     ~4,000,000 params  (targeting Q and V projections)
                         ─────────────────
Percentage trained:         ~0.06%
```


## Scaling Factor

```
output = W·x + (A·B·x) * (alpha / rank)
                          ───────────────
                          scaling factor

alpha = 16, rank = 8  →  scale = 2.0
alpha = 16, rank = 16 →  scale = 1.0
```

- Alpha controls how much the LoRA correction "matters"
- Higher alpha → stronger adaptation
- Typical: alpha = 2 × rank


## What to Say in Interviews

- "LoRA injects two small matrices A and B into each attention layer.
  The product A*B is a low-rank approximation of the weight update.
  This means we train less than 1% of the parameters while the original
  weights stay frozen."

- "The rank r controls the capacity of the adapter. r=8 is typical
  for style/tone tasks. r=64 might be needed for complex domain shifts."

- "At inference, the adapter adds a small correction to each layer's
  output. We can merge it into the base weights for zero overhead,
  or keep it separate for hot-swapping."


## TL;DR (Interview Summary)

- LoRA adds two small matrices (A, B) to each target layer — product A*B is the update
- Rank r is the bottleneck: r=8 means only 8-dimensional corrections per layer
- Trains ~0.1% of total parameters — rest stays frozen
- Scaling factor (alpha/rank) controls adaptation strength
- At inference: output = original + LoRA correction (can be merged for zero overhead)
- The "low-rank" assumption: most fine-tuning changes live in a low-dimensional subspace
