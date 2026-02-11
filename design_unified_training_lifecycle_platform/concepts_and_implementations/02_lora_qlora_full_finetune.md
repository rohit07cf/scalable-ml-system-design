# 02 — LoRA vs QLoRA vs Full Fine-Tuning


## Full Fine-Tuning

### What happens

- Every weight in the model gets updated during training
- You need the full model + gradients + optimizer state in GPU memory

### When to use

- You have **lots of GPUs** and budget is not a concern
- Task is **very different** from what the base model was pretrained on
- You need **maximum quality** and have enough data (100K+ examples)

### When NOT to use

- Limited GPU budget (most teams)
- Task is a style/tone shift (LoRA is enough)
- You need to serve multiple task variants (can't swap full models easily)

### Cost / memory

| Model | GPU Memory | Typical GPUs |
|---|---|---|
| 7B | ~56–84 GB | 2x A100 (80 GB) |
| 70B | ~560 GB | 8+ A100s |

### Interview phrasing

- "Full FT gives the best quality ceiling but costs 5–10x more than LoRA."
- "We'd only do full FT if the task domain is very far from pretraining data."
- "For most enterprise fine-tuning, LoRA gets 95% of the quality at 10% of the cost."


## LoRA (Low-Rank Adaptation)

### What happens

- Base model weights are **frozen** (loaded but not updated)
- Small **low-rank matrices** (A and B) are injected into attention layers
- Only A and B get trained
- **Rank** (r) controls adapter size: r=8 means 8-dimensional bottleneck

```
Original weight matrix W:  [4096 x 4096]  ← frozen

LoRA adds:
  A: [4096 x 8]    ← trainable  (small!)
  B: [8 x 4096]    ← trainable  (small!)

During forward pass:
  output = W·x + (A·B)·x
              ↑ original   ↑ LoRA update
```

> Think of it like: W is a huge whiteboard already written on.
> Instead of erasing and rewriting, you tape a small sticky note (A·B)
> on top that adds your corrections.

### When to use

- **Most fine-tuning tasks** — tone, style, domain adaptation
- Limited GPU budget
- Need to serve multiple adapters (swap sticky notes, not whiteboards)

### When NOT to use

- Task requires fundamentally new knowledge the base model doesn't have
- You need absolute maximum quality and cost doesn't matter

### Cost / memory

| Model | LoRA Memory | Adapter Size | Typical GPUs |
|---|---|---|---|
| 7B | ~16–20 GB | ~10–50 MB | 1x A100 |
| 70B | ~80–90 GB | ~50–200 MB | 2x A100 |

### Interview phrasing

- "LoRA freezes the base model and trains small low-rank matrices in attention layers."
- "Rank r controls the tradeoff — r=8 or r=16 is typical; higher rank = more capacity but more cost."
- "The adapter is tiny (tens of MB), so we can store and swap many adapters per base model."


## QLoRA (Quantized LoRA)

### What happens

- Base model is **quantized to 4-bit** (shrunk ~4x in memory)
  - Quantization = represent weights with fewer bits (less precision, much smaller)
- LoRA adapters are trained in **full precision** (16-bit) on top
- Computation uses a trick called "double quantization" to stay accurate

```
Full precision:  each weight = 16 bits  →  7B model ≈ 14 GB
4-bit quantized: each weight = 4 bits   →  7B model ≈ 3.5 GB
                                            + LoRA adapters ≈ 50 MB (16-bit)
                                            Total ≈ ~6–8 GB
```

> Think of it like: you shrink the whiteboard to a thumbnail (4-bit),
> but your sticky notes (LoRA) are still full-size and precise.

### When to use

- **Tightest GPU budget** — fine-tune 7B on a single 24 GB GPU
- Quality is surprisingly close to full LoRA (within 1–2%)
- Great for experimentation and HPO sweeps (more trials per GPU)

### When NOT to use

- You need maximum inference speed (quantized models are slightly slower)
- Some quantization formats don't support all model architectures yet

### Cost / memory

| Model | QLoRA Memory | Typical GPUs |
|---|---|---|
| 7B | ~6–8 GB | 1x RTX 4090 or 1x A100 |
| 13B | ~10–14 GB | 1x A100 |
| 70B | ~36–48 GB | 1x A100 (80 GB) |

### Interview phrasing

- "QLoRA quantizes the base to 4-bit and trains LoRA adapters in 16-bit on top."
- "It lets you fine-tune a 7B model on a single consumer GPU."
- "Quality loss vs full-precision LoRA is minimal — typically within 1–2%."


## Side-by-Side Comparison

| | Full FT | LoRA | QLoRA |
|---|---|---|---|
| **What's trained** | All weights | Small adapter matrices | Small adapter matrices |
| **Base model** | Updated | Frozen (16-bit) | Frozen (4-bit) |
| **GPU memory (7B)** | ~60–80 GB | ~16–20 GB | ~6–8 GB |
| **Adapter size** | N/A (full model) | ~10–50 MB | ~10–50 MB |
| **Quality** | Best | ~95–99% of full | ~93–98% of full |
| **Training speed** | Slowest | Fast | Fast |
| **Multi-adapter serving** | Hard (swap full models) | Easy (swap adapters) | Easy (swap adapters) |
| **When to use** | Unlimited budget, max quality | Default choice | Tight budget, experimentation |


## Common Mistakes

- Thinking LoRA trains a "separate small model" — it doesn't.
  It injects matrices INTO the existing model architecture.

- Confusing adapter size with model size — the adapter is ~50 MB,
  but you still need the base model loaded to use it.

- Thinking QLoRA quality is bad — it's surprisingly good.
  The 4-bit quantization affects the base, but the adapter trains
  in full precision where it matters.


## TL;DR (Interview Summary)

- **Full FT**: update all weights, best quality, ~60–80 GB for 7B, expensive
- **LoRA**: freeze base, train small low-rank matrices, ~16–20 GB for 7B, 95%+ quality
- **QLoRA**: quantize base to 4-bit + LoRA in 16-bit, ~6–8 GB for 7B, 93%+ quality
- LoRA rank (r) controls adapter capacity — r=8 or 16 is typical
- Adapter is tiny (~50 MB) — easy to store, swap, version
- Default choice for most teams: **LoRA** (or QLoRA if budget is very tight)
- Full FT only when domain shift is extreme and budget allows
- In interviews: "freeze base, train small adapter" covers 90% of questions
