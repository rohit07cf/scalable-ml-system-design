# Diagram: Tensor Parallel vs Data Parallel


## Data Parallel (DP) — Independent Replicas

```
                 ┌──────────────┐
                 │ Load Balancer│
                 └──────┬───────┘
            ┌───────────┼───────────┐
            ▼           ▼           ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │   GPU 0    │ │   GPU 1    │ │   GPU 2    │
     │            │ │            │ │            │
     │ ┌────────┐ │ │ ┌────────┐ │ │ ┌────────┐ │
     │ │ Full   │ │ │ │ Full   │ │ │ │ Full   │ │
     │ │ Model  │ │ │ │ Model  │ │ │ │ Model  │ │
     │ │ (copy) │ │ │ │ (copy) │ │ │ │ (copy) │ │
     │ └────────┘ │ │ └────────┘ │ │ └────────┘ │
     │            │ │            │ │            │
     │ Handles    │ │ Handles    │ │ Handles    │
     │ req 1,4,7  │ │ req 2,5,8  │ │ req 3,6,9  │
     └────────────┘ └────────────┘ └────────────┘

     NO communication between GPUs during inference.
     Each GPU processes requests independently.
     Throughput scales linearly: 3 GPUs = ~3× throughput.
```


## Tensor Parallel (TP) — Split One Model

```
     One request flows through ALL GPUs:

     ┌────────────────────────────────────────────────┐
     │                  One Request                   │
     └────────────────────┬───────────────────────────┘
                          │
                          ▼
     ┌──────────────────────────────────────────────┐
     │              Layer 1                         │
     │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
     │  │  GPU 0   │  │  GPU 1   │  │  GPU 2   │   │
     │  │ columns  │  │ columns  │  │ columns  │   │
     │  │ 0–1365   │  │1366–2730 │  │2731–4095 │   │
     │  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
     │       └──────all-reduce──────────┘           │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │              Layer 2                         │
     │  (same split pattern)                        │
     │       └──────all-reduce──────────┘           │
     └──────────────────────┬───────────────────────┘
                            │
                            ▼
                      ... repeat for all layers ...
                            │
                            ▼
                       Final output

     Communication: all-reduce at EVERY layer boundary.
     Needs fast interconnect (NVLink).
```


## Side-by-Side Comparison

```
                   Data Parallel          Tensor Parallel
                   ─────────────          ───────────────
Model per GPU:     FULL copy              1/N of each layer

Communication:     NONE (inference)       All-reduce per layer
                                          (every forward pass!)

Latency:           Same as 1 GPU          Can be LOWER (smaller
                                          matrix multiplications)
                                          but communication adds up

Throughput:        Linear scaling         ~Same as 1 replica
                   (N GPUs = N×)          (but can handle larger model)

Memory per GPU:    Full model + KV cache  1/N model + full KV cache

Best for:          Model FITS on 1 GPU    Model DOESN'T FIT on 1 GPU
                   + need throughput       + need to serve it at all
```


## When to Use Which (Decision Tree)

```
Does the model fit on 1 GPU?
  │
  ├── YES → Data Parallel (replicas)
  │         → each GPU = independent server
  │         → throughput scales linearly
  │
  └── NO  → Tensor Parallel (split model)
            │
            ├── Fits on 1 NODE (multi-GPU)?
            │   └── TP within the node (NVLink is fast)
            │
            └── Doesn't fit on 1 node?
                └── TP within node + DP across nodes
                    (each node = one TP group = one replica)
```

### Concrete examples

| Model | GPUs | Strategy | Why |
|---|---|---|---|
| 7B | 4× A100 80 GB | **DP=4** | 7B fits on 1 GPU; 4 replicas |
| 70B | 4× A100 80 GB | **TP=4** | 70B doesn't fit on 1 A100 |
| 70B | 8× A100 80 GB | **TP=4, DP=2** | 2 replicas, each split across 4 GPUs |
| 7B | 2 nodes × 4 GPUs | **DP=8** | 8 independent replicas |
| 70B | 2 nodes × 4 GPUs | **TP=4, DP=2** | TP within each node, DP across nodes |


## Training vs Inference (Data Parallel Differs!)

```
         TRAINING DP                    INFERENCE DP
         ───────────                    ────────────
  Each GPU: full model copy      Each GPU: full model copy
  Data: split across GPUs        Requests: routed to any GPU
  Communication: all-reduce      Communication: NONE
                 gradients
  Purpose: faster training       Purpose: more throughput
```

Key difference: at inference there's no gradient sync —
replicas are fully independent.


## What to Say in Interviews

- "Data parallel inference runs independent model replicas on separate
  GPUs. There's no communication between them — each handles its own
  requests. Throughput scales linearly with the number of replicas."

- "Tensor parallel splits one model across GPUs. Each layer is divided
  across GPUs with an all-reduce at every layer boundary. It's needed
  when the model doesn't fit on a single GPU."

- "The rule of thumb is: use data parallel when the model fits on one
  GPU (for throughput), tensor parallel when it doesn't (to make it
  serveable), and combine both for large-scale deployments."


## TL;DR (Interview Summary)

- Data parallel inference: full model per GPU, no communication, linear throughput
- Tensor parallel inference: split model across GPUs, all-reduce per layer
- DP for throughput (model fits on 1 GPU); TP for large models (doesn't fit)
- TP needs fast interconnect (NVLink) — don't use TP across network nodes
- Combine TP+DP for large-scale: TP within a node, DP across nodes
- At inference, DP replicas are fully independent — no gradient sync
- Decision: model fits on 1 GPU → DP; doesn't fit → TP; need both → TP+DP
