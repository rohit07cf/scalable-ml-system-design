# 02 — Distributed Inference Concepts


## Key Terms (One Line Each)

- **Throughput** — how many requests you can serve per second (higher = better)
- **Latency** — how long one request takes end-to-end (lower = better)
- **Batching** — grouping multiple requests together and processing them at once
- **Dynamic batching** — adding new requests to a running batch on the fly
- **KV cache** — stored key/value tensors from previous tokens (avoids recomputation)
- **Tensor Parallel (TP)** — split one model's layers across GPUs (for large models)
- **Data Parallel (DP) inference** — run independent model replicas on different GPUs
- **Prefill** — processing all input tokens at once (compute-heavy)
- **Decode** — generating output tokens one at a time (memory-heavy, KV cache grows)


## Throughput vs Latency

These are the two axes of inference performance:

| | Optimized by |
|---|---|
| **Latency** (fast single request) | Fewer layers per GPU (tensor parallel), fast decode |
| **Throughput** (many requests/sec) | Larger batches, more replicas, continuous batching |

> Think of it like a restaurant:
> - **Latency** = how fast one customer gets their food
> - **Throughput** = how many customers you serve per hour
>
> Bigger kitchen (more GPUs) helps both, but there are tradeoffs.

Usually: batch more → higher throughput, slightly higher latency per request.


## Batching

### Static batching (simple)

- Collect N requests, run them together, return all results
- Problem: fast requests wait for slow ones ("head-of-line blocking")

### Dynamic / continuous batching (production)

- New requests join a running batch as slots free up
- Each request can finish independently
- **Much better** throughput and latency

```
Time →
Slot 0: [req A ██████████]  [req D ████████]
Slot 1: [req B ████]  [req E ██████████████████]
Slot 2: [req C ████████████████]  [req F ██████]

Requests join/leave the batch independently.
No waiting for the slowest request.
```

> Think of it like: a conveyor belt at a sushi restaurant.
> New dishes appear continuously; you grab yours when it's ready.
> Nobody waits for everyone to finish eating.


## KV Cache — What It Is and Why It Matters

### The problem

When generating token N+1, the model needs to "look at" all previous tokens (1 to N).

**Without KV cache**: recompute attention for ALL previous tokens every step. Slow.

**With KV cache**: store the Key and Value tensors from previous tokens.
At step N+1, only compute for the new token and look up the cached K/V.

```
Step 1: Process "Hello"        → cache K1, V1
Step 2: Process "world"        → cache K2, V2  (reuse K1, V1)
Step 3: Process "how"          → cache K3, V3  (reuse K1, V1, K2, V2)
...
Step N: Process token N        → reuse all cached K, V from steps 1..N-1
```

### Why it's the memory bottleneck

For each request in the batch, the KV cache grows with sequence length:

```
KV cache per request ≈ 2 × num_layers × hidden_dim × seq_len × dtype_size

Example (7B model, 2K tokens, fp16):
  2 × 32 layers × 4096 hidden × 2048 seq × 2 bytes = ~1 GB per request

Batch of 16 requests = ~16 GB just for KV cache!
```

This limits how many concurrent requests you can serve.


### KV cache pitfalls and memory pressure

- Long sequences eat KV memory fast → fewer concurrent requests
- If you run out of GPU memory → requests get queued or OOM crash
- Solutions:
  - **PagedAttention** (vLLM) — allocate KV cache in pages, like OS virtual memory
  - **KV cache eviction** — drop old tokens for very long conversations
  - **Quantized KV cache** — store K/V in lower precision (fp8)

> Think of it like: each customer at the restaurant takes up table space.
> Longer meals = fewer tables available = fewer customers served.


## Data Parallel vs Tensor Parallel Inference

### Data Parallel (DP) inference

- Run **independent replicas** of the full model on different GPUs
- Each replica handles different requests
- **No communication** between replicas during inference

```
GPU 0: [Full model] ← handles requests 1, 3, 5
GPU 1: [Full model] ← handles requests 2, 4, 6
```

- When: model fits on 1 GPU, need more throughput
- Pro: simple, linear throughput scaling, no GPU-to-GPU communication
- Con: each GPU needs enough memory for full model + KV cache

### Tensor Parallel (TP) inference

- **Split one model** across multiple GPUs
- Each GPU holds part of every layer
- GPUs must communicate at every layer boundary

```
GPU 0: [Layer 1a, Layer 2a, ...] ─┐
                                    ├── all-reduce at each layer
GPU 1: [Layer 1b, Layer 2b, ...] ─┘
```

- When: model is too large for 1 GPU
- Pro: can serve models that don't fit in one GPU's memory
- Con: all-reduce at every layer → latency overhead, needs fast interconnect


### Choosing between them

| Scenario | Best approach |
|---|---|
| 7B model, 4× A100 80 GB | **DP**: 4 replicas, 4× throughput |
| 70B model, 4× A100 80 GB | **TP=4**: model split across all 4 GPUs |
| 70B model, 8× A100 80 GB | **TP=4, DP=2**: 2 replicas, each split across 4 GPUs |


## Single-Node vs Multi-Node Serving

### Single-node multi-GPU

- All GPUs on one machine — fast NVLink communication
- TP is practical here (low latency between GPUs)
- Simpler deployment: one process, one machine

### Multi-node serving

- Separate machines, each running a model replica
- **Load balancer** distributes requests across replicas
- TP across nodes is usually **too slow** (network latency per layer)
- Preferred pattern: **DP across nodes** (each node = independent replica)

```
                    ┌──────────────┐
                    │Load Balancer │
                    └──────┬───────┘
                  ┌────────┼────────┐
                  ▼        ▼        ▼
            ┌──────┐ ┌──────┐ ┌──────┐
            │Node 0│ │Node 1│ │Node 2│
            │(full │ │(full │ │(full │
            │model)│ │model)│ │model)│
            └──────┘ └──────┘ └──────┘
```

- Each node is a fully independent serving replica
- Load balancer routes requests round-robin or least-connections
- Shared model artifacts: all nodes pull from S3/shared storage


## Behind the Scenes: Request Lifecycle (10 bullets)

1. **Client** sends POST request to inference endpoint
2. **Load balancer** picks a healthy replica (round-robin or least-connections)
3. **Server** receives request, tokenizes the prompt
4. **Scheduler** adds the request to the dynamic batch
5. **Prefill phase**: all input tokens processed in parallel (compute-heavy)
6. **KV cache allocated** for this request (per-token key/value tensors)
7. **Decode phase**: generate tokens one at a time, each step reads KV cache
8. **Stop condition**: EOS token or max_length reached
9. **Detokenize** and return the response (streaming or complete)
10. **KV cache freed** for this request → slot available for next request


## Common Interview Traps

- **"More GPUs always means lower latency"** — NO. TP adds communication
  overhead. Beyond 4–8 GPUs, latency may increase.

- **"KV cache is small"** — NO. It's often the #1 memory consumer
  at inference time, especially with long sequences.

- **"Tensor parallel across nodes works well"** — NOT usually. Network
  latency at every layer makes it impractical. Use DP across nodes.

- **"Static batching is fine for production"** — NO. Static batching
  wastes GPU cycles waiting for the slowest request. Use continuous batching.


## TL;DR (Interview Summary)

- Throughput = requests/sec; latency = time per request — batching helps throughput
- Dynamic/continuous batching: requests join and leave independently — production standard
- KV cache stores previous tokens' keys/values — avoids recomputation but eats memory
- KV cache is the #1 memory bottleneck at inference — limits batch size
- Data parallel inference: independent replicas, no communication, scales throughput linearly
- Tensor parallel inference: split model across GPUs, all-reduce per layer — for large models
- Multi-node serving: DP replicas behind a load balancer (not TP across network)
- Request lifecycle: tokenize → batch → prefill → decode (KV cache) → detokenize → respond
