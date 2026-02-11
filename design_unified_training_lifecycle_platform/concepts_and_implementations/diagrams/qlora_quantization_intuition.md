# Diagram: QLoRA Quantization Intuition


## The Core Idea

QLoRA = **Quantize the base model** (shrink it) + **train LoRA adapters in full precision**.

You get the memory savings of both quantization AND LoRA.


## What Is Quantization?

- Each model weight is a number (e.g., 0.00347)
- In 16-bit: each weight takes 2 bytes → 7B model = 14 GB
- In 4-bit: each weight takes 0.5 bytes → 7B model = 3.5 GB
- **Trade-off**: less precision per weight, but 4x less memory

> Think of it like: instead of recording temperature as "72.347°F",
> you round it to "72°F". Less precise, but takes way less space.
> For most purposes, the rounded version works fine.


## ASCII Diagram

```
              STANDARD LoRA                        QLoRA
              ─────────────                        ─────

    ┌────────────────────────┐       ┌────────────────────────┐
    │   Base Model (16-bit)  │       │  Base Model (4-bit)    │
    │   FROZEN               │       │  FROZEN + QUANTIZED    │
    │                        │       │                        │
    │   7B → 14 GB           │       │   7B → 3.5 GB          │
    └────────────┬───────────┘       └────────────┬───────────┘
                 │                                │
                 +                                +
                 │                                │
    ┌────────────┴───────────┐       ┌────────────┴───────────┐
    │   LoRA Adapters        │       │   LoRA Adapters         │
    │   (16-bit, trainable)  │       │   (16-bit, trainable)   │
    │   ~50 MB               │       │   ~50 MB                │
    └────────────────────────┘       └────────────────────────┘

    Total: ~16–20 GB                 Total: ~6–8 GB
    GPU:   1× A100                   GPU:   1× RTX 4090 (24 GB)
```


## How QLoRA Works (Step by Step)

```
1. Load base model in 4-bit quantization
   ┌───────────────────────────────────────┐
   │  Normal:  weight = 0.00347  (16 bits) │
   │  4-bit:   weight ≈ 0.004   (4 bits)  │
   │                                        │
   │  Uses NF4 (NormalFloat4) format        │
   │  — optimized for neural network        │
   │    weight distributions                │
   └───────────────────────────────────────┘

2. Attach LoRA adapters in 16-bit
   ┌───────────────────────────────────────┐
   │  Adapters are small (~50 MB)          │
   │  Keeping them in 16-bit = full        │
   │  precision where it matters           │
   │  (the part that's actually learning)  │
   └───────────────────────────────────────┘

3. Forward pass:
   ┌───────────────────────────────────────┐
   │  Dequantize W (4-bit → 16-bit)       │
   │  on the fly during computation        │
   │                                        │
   │  output = dequant(W)·x + (A·B)·x     │
   │           ↑ base (was 4-bit)  ↑ LoRA  │
   └───────────────────────────────────────┘

4. Backward pass:
   ┌───────────────────────────────────────┐
   │  Gradients flow through dequantized W │
   │  but ONLY update A and B              │
   │  W stays in 4-bit, unchanged          │
   └───────────────────────────────────────┘
```


## Memory Breakdown (7B Model)

```
                  Full FT      LoRA        QLoRA
                  ───────      ────        ─────
Base model:       14 GB        14 GB       3.5 GB    (4-bit)
Gradients:        14 GB        —           —
Optimizer:        28 GB        ~0.2 GB     ~0.2 GB
LoRA adapters:    —            ~0.05 GB    ~0.05 GB
Activations:      ~8 GB        ~4 GB       ~4 GB
                  ────────     ────────    ────────
Total:            ~64 GB       ~18 GB      ~8 GB
GPUs needed:      2× A100      1× A100     1× RTX 4090
```


## Double Quantization (QLoRA's Extra Trick)

```
Normal quantization:
  weights → 4-bit + quantization constants (16-bit per block)

Double quantization:
  weights → 4-bit + quantization constants → quantize the constants too!

Saves: ~0.4 GB for a 7B model (small but it adds up)
```

WHY it matters: every GB saved = more room for batch size or longer sequences.


## Quality Impact

```
                     Quality (relative to Full FT)
Full fine-tuning:    100%   (reference)
LoRA (16-bit base):  ~97%
QLoRA (4-bit base):  ~95%   ← only ~2% below LoRA

The 2% quality drop is usually acceptable for:
  ✓ Tone/style adaptation
  ✓ Domain-specific formatting
  ✓ Customer support, summarization, classification
```

- For cutting-edge reasoning tasks on huge models, full-precision LoRA may matter
- For most enterprise tasks, QLoRA is plenty


## What to Say in Interviews

- "QLoRA quantizes the base model to 4-bit and trains LoRA adapters in
  full 16-bit precision. This cuts GPU memory roughly in half compared
  to standard LoRA, letting you fine-tune a 7B model on a single 24 GB
  consumer GPU."

- "The key insight is that quantization loses some precision in the frozen
  base, but the LoRA adapters — the part that's actually learning — stay
  in full precision. So the quality loss is minimal."

- "In a platform context, QLoRA is great for HPO sweeps because you can
  fit more trials per GPU, reducing the cost of hyperparameter search."


## TL;DR (Interview Summary)

- QLoRA = 4-bit quantized base model + 16-bit LoRA adapters
- Cuts memory from ~18 GB to ~8 GB for a 7B model
- Quality loss vs LoRA is only ~2% — acceptable for most tasks
- Enables fine-tuning on consumer GPUs (RTX 4090, 24 GB)
- Forward pass: dequantize on-the-fly, compute, gradients only update LoRA
- Double quantization saves extra memory by quantizing the quantization constants
- Best for: tight budget, HPO sweeps (more trials per GPU), experimentation
