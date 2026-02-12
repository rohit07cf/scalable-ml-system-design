# 03 — Parallelism and Efficiency


## Why Parallelism Is Required

A single GPU cannot hold a frontier model in memory, let alone train it.

- **70B model in fp16**: ~140 GB just for weights
- **Training state** (gradients + optimizer): ~3–4x weight memory
- **70B total training memory**: ~420–560 GB
- **Single A100/H100**: 80 GB

You need to split the work across hundreds to thousands of GPUs.
Frontier models combine **multiple parallelism strategies simultaneously**.


## Parallelism Strategies

### Data Parallelism (DP / DDP / FSDP / ZeRO)

- **Concept**: replicate the model, split the data
- Each GPU processes a different mini-batch
- Gradients are averaged via all-reduce
- **DDP**: full model copy per GPU, all-reduce gradients only
- **FSDP / ZeRO**: shard model weights + gradients + optimizer across GPUs

| Variant | Model Replicated? | What's Sharded? | Memory per GPU |
|---|---|---|---|
| DDP | Yes (full copy) | Nothing | Full model + grads + optimizer |
| ZeRO Stage 1 | Yes (full copy) | Optimizer state | Model + grads |
| ZeRO Stage 2 | Yes (full copy) | Optimizer + gradients | Model only |
| ZeRO Stage 3 / FSDP | No (sharded) | Everything | 1/N of everything |


### Tensor Parallelism (TP)

- **Concept**: split individual layers across GPUs
- Each GPU computes part of every matrix multiplication
- All-reduce at every layer boundary
- **Requires fast interconnect** (NVLink) — not practical across network nodes

Typical: TP=4 or TP=8 within a single node (GPUs connected by NVLink).


### Pipeline Parallelism (PP)

- **Concept**: split the model by layers — each GPU gets a group of layers
- Data flows through GPUs in sequence (like a pipeline)
- **Micro-batching**: split a batch into micro-batches to keep all stages busy
- Avoids the "pipeline bubble" (idle time) by overlapping micro-batches

Typical: PP=4 to PP=16 for very deep models.


### Sequence Parallelism (SP)

- **Concept**: split the sequence dimension across GPUs
- Each GPU processes a portion of the token sequence
- Useful for very long sequences (32K–1M+ tokens)
- Often combined with TP — handles the parts of computation that TP doesn't parallelize
  (e.g., LayerNorm, dropout, activation checkpointing regions)


### Mixture-of-Experts (MoE)

- **Concept**: not all parameters are active for every token
- Model has N experts (e.g., 128); only K are active per token (e.g., 16)
- A **router** selects which experts process each token
- **Total params** can be very large (e.g., 1T+) while **active params** stay manageable

| Aspect | Dense Model | MoE Model |
|---|---|---|
| Total params | 70B | 1T+ |
| Active params per token | 70B (all) | 50–100B (subset) |
| FLOPs per token | Proportional to total | Proportional to active |
| Memory | Full model | Full model (all experts loaded) |
| Throughput | Lower (at same param count) | Higher |


## Parallelism Comparison Table

| Strategy | Model Replicated? | Where Parallelism Applied | Memory Scaling | Communication Pattern |
|---|---|---|---|---|
| **DP / DDP** | Yes | Data (different batches) | None (full copy each) | All-reduce gradients |
| **FSDP / ZeRO-3** | No (sharded) | Data + model state | 1/N per GPU | All-gather + reduce-scatter |
| **Tensor Parallel** | No (split layers) | Within each layer | 1/N per layer | All-reduce per layer |
| **Pipeline Parallel** | No (split by layers) | Across layer groups | Subset of layers per GPU | Point-to-point (stage to stage) |
| **Sequence Parallel** | No | Along token sequence | Reduced activation memory | All-gather / reduce-scatter |
| **MoE** | Experts distributed | Expert selection per token | Experts spread across GPUs | All-to-all (token routing) |


## How Frontier Models Combine Parallelism

No single strategy is enough. Real frontier training uses **3–5 strategies at once**.

### Typical configuration (100B+ dense model on 1000+ GPUs)

```
DP (data parallel)  = 64 replicas
  × TP (tensor parallel) = 8 GPUs per node
  × PP (pipeline parallel) = 2 stages
  = 64 × 8 × 2 = 1,024 GPUs

Within each node:  TP=8 (NVLink)
Across nodes:      DP + PP (network)
```

### Typical MoE configuration

```
DP = 32 replicas
  × TP = 8 within node
  × EP (expert parallel) = experts spread across DP groups
  = 256+ GPUs, with all-to-all routing for expert dispatch
```


## Efficiency Techniques

### Mixed Precision (bfloat16, FP8)

| Precision | Bits | Memory | Speed | Quality | Use Case |
|---|---|---|---|---|---|
| FP32 | 32 | Baseline | Baseline | Best | Rarely used for training |
| BF16 | 16 | 2x smaller | ~2x faster | Excellent | **Standard for training (2024–2026)** |
| FP16 | 16 | 2x smaller | ~2x faster | Good (needs scaling) | Older GPUs (V100) |
| FP8 | 8 | 4x smaller | ~4x faster | Good (with care) | **Emerging for Blackwell (2025–2026)** |

- **BF16** is the standard training precision in 2026
- **FP8** is supported on Blackwell GPUs (B200/GB200) — 2x faster than BF16
  - Requires careful calibration; adoption is growing


### FlashAttention (v2/v3)

- Fuses attention computation into a single GPU kernel
- **Eliminates** the materialization of the N x N attention matrix
- Memory: O(N) instead of O(N^2) for sequence length N
- Speed: 2–4x faster attention computation
- **FlashAttention-3** (Blackwell): leverages new hardware features (TMA, WGMMA)
- Standard in all frontier training by 2026 — not optional


### Activation Checkpointing (Gradient Checkpointing)

- Instead of storing all activations for backward pass, **recompute** them
- Trades ~30% extra compute for ~60–70% less activation memory
- Enables training with larger batch sizes or longer sequences
- **Selective checkpointing**: only recompute expensive layers (attention), keep cheap ones


## Why Data Parallelism Remains the Backbone in 2026

- **Simplest** to implement and scale
- **Linear throughput scaling**: N GPUs = ~N x throughput
- TP and PP handle the "model doesn't fit" problem
- DP handles the "need more throughput" problem
- Combined: TP+PP to fit the model, DP to scale throughput
- With ZeRO/FSDP, even the memory problem is solved within the DP framework

> In interviews: "DP gives you throughput scaling. TP and PP give you memory
> scaling. You combine them: TP within a node for fast communication, PP across
> a few stages, and DP across everything else for throughput."


## TL;DR (Interview Summary)

- DP = split data, replicate model — backbone of all distributed training
- TP = split layers across GPUs within a node (needs NVLink)
- PP = split model into stages across nodes (pipeline with micro-batches)
- FSDP / ZeRO-3 = shard everything — 1/N memory per GPU
- MoE = many experts, few active per token — scale params without scaling FLOPs
- Real frontier training combines DP + TP + PP + ZeRO + MoE simultaneously
- BF16 is standard precision; FP8 is emerging on Blackwell GPUs
- FlashAttention is mandatory — O(N) memory, 2–4x faster attention
