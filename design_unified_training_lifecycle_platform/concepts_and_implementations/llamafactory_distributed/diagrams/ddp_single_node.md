# Diagram: DDP on a Single Node


## ASCII Diagram

```
┌───────────────────────────────────────────────────────────┐
│                    Single Machine                         │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  GPU 0   │  │  GPU 1   │  │  GPU 2   │  │  GPU 3   │ │
│  │          │  │          │  │          │  │          │ │
│  │ Full     │  │ Full     │  │ Full     │  │ Full     │ │
│  │ Model    │  │ Model    │  │ Model    │  │ Model    │ │
│  │ Copy     │  │ Copy     │  │ Copy     │  │ Copy     │ │
│  │          │  │          │  │          │  │          │ │
│  │ Batch    │  │ Batch    │  │ Batch    │  │ Batch    │ │
│  │ 1/4      │  │ 2/4      │  │ 3/4      │  │ 4/4      │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │              │              │       │
│       │         ┌────┴──────────────┴────┐         │       │
│       └────────>│     ALL-REDUCE         │<────────┘       │
│                 │  (average gradients)   │                 │
│                 │  via NVLink / PCIe     │                 │
│                 │  ~300–900 GB/s         │                 │
│                 └────────────────────────┘                 │
│                          │                                │
│                          ▼                                │
│               All GPUs apply the SAME                     │
│               averaged gradient update                    │
│               → models stay in sync                       │
└───────────────────────────────────────────────────────────┘
```


## Plain-English Explanation

1. One machine with N GPUs (typically 4 or 8)
2. Each GPU loads a **complete copy** of the model
3. The training data is split into N equal chunks — each GPU gets a different chunk
4. Each GPU does its own forward + backward pass independently
5. After backward pass, **all-reduce** averages the gradients across all GPUs
6. All-reduce happens over **NVLink** (very fast, 300–900 GB/s)
7. Each GPU applies the averaged gradient → models stay perfectly in sync
8. This is the simplest distributed setup — one command, no network config

Key insight: the only communication is the gradient all-reduce.
Everything else (forward, backward, optimizer step) is independent per GPU.


## What to Say in Interviews

- "DDP on a single node gives each GPU a full model copy and a different
  data slice. The only synchronization point is an all-reduce after the
  backward pass to average gradients."

- "Single-node DDP is the simplest distributed setup because all GPUs
  communicate via NVLink, which is 300–900 GB/s — the all-reduce is
  essentially free."

- "With LoRA, the all-reduce payload is ~8 MB instead of 14 GB, so the
  communication overhead is negligible even without NVLink."


## TL;DR (Interview Summary)

- Each GPU: full model copy + different data slice
- Only sync point: all-reduce to average gradients after backward pass
- NVLink makes intra-node all-reduce nearly free (~300–900 GB/s)
- Effective batch size = per_gpu_batch × num_gpus
- LoRA all-reduce is ~8 MB — essentially zero overhead
- Launch: `torchrun --nproc_per_node=N` — one command, no network config
