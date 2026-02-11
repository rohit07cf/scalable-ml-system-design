# Diagram: Inference Batching & KV Cache


## Dynamic Batching

```
Time ────────────────────────────────────────────────>

                    Batch window
              ┌─────────────────────────┐
              │                         │
  Req A ──────┤██████████████████       │  (long response)
              │                         │
  Req B ──────┤████████  ✓ done         │  (short response)
              │         │               │
  Req D ─────────────────┤██████████████│  (fills B's slot)
              │                         │
  Req C ──────┤██████████████  ✓ done   │
              │               │         │
  Req E ──────────────────────┤█████████│  (fills C's slot)
              │                         │
              └─────────────────────────┘

  Static batching:  wait for ALL to finish → waste GPU cycles
  Dynamic batching: new requests fill finished slots → always busy
```


## Why Dynamic Batching Matters

- LLM decoding is **memory-bound**, not compute-bound
- GPU has spare compute even while decoding — can handle more requests
- Dynamic batching keeps the GPU busy by filling empty slots immediately
- Result: **2–5x higher throughput** vs static batching


## KV Cache — How It Works

```
   Generating: "Hello world how are you"
                                          KV Cache
   Step 1: Process "Hello"                ┌──────────┐
           → generate K₁, V₁             │ K₁, V₁   │
                                          └──────────┘

   Step 2: Process "world"                ┌──────────┐
           → reuse K₁, V₁ from cache     │ K₁, V₁   │
           → generate K₂, V₂             │ K₂, V₂   │
                                          └──────────┘

   Step 3: Process "how"                  ┌──────────┐
           → reuse K₁, V₁, K₂, V₂       │ K₁, V₁   │
           → generate K₃, V₃             │ K₂, V₂   │
                                          │ K₃, V₃   │
                                          └──────────┘

   ...cache grows with each token...

   Step N: Process token N                ┌──────────┐
           → reuse ALL cached K, V        │ K₁..Kₙ   │
           → generate Kₙ, Vₙ             │ V₁..Vₙ   │
                                          └──────────┘
```


## KV Cache Memory Math

```
KV cache per token per layer = 2 × hidden_dim × dtype_size
                             = 2 × 4096 × 2 bytes (fp16)
                             = 16 KB

KV cache per token (all layers) = 16 KB × 32 layers = 512 KB

For a 2048-token sequence:
  512 KB × 2048 = 1 GB per request

For a batch of 16 requests:
  1 GB × 16 = 16 GB  ← just for KV cache!

Model weights (7B fp16) = 14 GB

Total: 14 GB (model) + 16 GB (KV cache) = 30 GB
       ↑ fixed                ↑ grows with batch size + seq length
```


## KV Cache Is the Bottleneck

```
┌─────────────────────────────────────────────────┐
│                GPU Memory (80 GB)                │
│                                                  │
│  ┌──────────────────┐                            │
│  │   Model Weights  │  14 GB  (fixed)            │
│  │   (7B, fp16)     │                            │
│  └──────────────────┘                            │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │         KV Cache                          │    │
│  │  grows with batch_size × seq_length       │    │
│  │                                           │    │
│  │  batch=8, 2K tokens:  8 GB               │    │
│  │  batch=16, 2K tokens: 16 GB              │    │
│  │  batch=32, 2K tokens: 32 GB              │    │
│  │  batch=16, 8K tokens: 64 GB   ← OOM!    │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────┐                            │
│  │  Activations +   │  ~2–4 GB (varies)          │
│  │  scratch space   │                            │
│  └──────────────────┘                            │
└─────────────────────────────────────────────────┘

More concurrent requests = more KV cache = less room
Longer sequences = more KV cache per request = fewer concurrent requests
```


## PagedAttention (vLLM's Solution)

```
Traditional KV cache:
  Pre-allocate contiguous memory per request
  → waste memory on short sequences
  → can't reuse freed memory easily

PagedAttention:
  Allocate KV cache in small pages (like OS virtual memory)
  → no wasted memory
  → pages freed instantly when request finishes
  → other requests can use those pages immediately

  Result: ~2–4x more concurrent requests in the same GPU memory
```

> Think of it like: traditional = reserve a whole table for each customer
> even if they're eating alone. PagedAttention = share tables, add/remove
> chairs as needed.


## What to Say in Interviews

- "KV cache stores key/value tensors from previous tokens to avoid
  recomputation. It grows linearly with sequence length and batch size,
  making it the primary memory bottleneck at inference time."

- "Dynamic batching lets new requests fill slots freed by completed
  requests, keeping the GPU fully utilized. vLLM's continuous batching
  can achieve 2–5x higher throughput than static batching."

- "PagedAttention from vLLM manages KV cache like virtual memory pages,
  eliminating fragmentation and enabling 2–4x more concurrent requests
  in the same GPU memory."


## TL;DR (Interview Summary)

- KV cache = stored key/value tensors; avoids recomputing attention for past tokens
- KV cache grows with: batch_size × sequence_length × layers × hidden_dim
- It's the #1 memory bottleneck at inference — determines max concurrent requests
- Dynamic batching: new requests fill completed slots — GPU stays busy
- Static batching wastes GPU time waiting for the slowest request
- PagedAttention (vLLM): manage KV in pages — 2–4x more concurrent requests
- Memory split: model weights (fixed) + KV cache (variable) + scratch space
