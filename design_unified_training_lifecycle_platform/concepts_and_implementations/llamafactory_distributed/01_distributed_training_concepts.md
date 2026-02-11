# 01 — Distributed Training Concepts


## Key Terms (One Line Each)

- **Data Parallelism (DP)** — each GPU gets a full model copy; data is split across GPUs
- **DDP (Distributed Data Parallel)** — PyTorch's efficient DP; one process per GPU
- **FSDP (Fully Sharded Data Parallel)** — shard model weights across GPUs to save memory
- **All-reduce** — operation where every GPU sends its gradients and gets back the average
- **NCCL** — NVIDIA's GPU-to-GPU communication library (pronounced "nickel")
- **Rank** — unique ID for each process (GPU) in a distributed job (0, 1, 2, …)
- **World size** — total number of processes (GPUs) across all nodes
- **Rendezvous** — how processes find each other to form a group


## Data Parallelism / DDP — The Default

### What happens (plain English)

Every GPU gets:
- A **full copy** of the model
- A **different slice** of the training data

After each forward+backward pass:
- Each GPU has gradients computed on its own data slice
- **All-reduce** averages the gradients across all GPUs
- Every GPU applies the same averaged gradient → models stay in sync

> Think of it like: 4 students each read a different chapter
> of the same textbook, then share their notes.
> Everyone ends up with the same combined knowledge.


### Why Gradients Need All-Reduce

Without syncing gradients:
- Each GPU would learn from only its own data slice
- Models would diverge → garbage results

All-reduce ensures every GPU takes the **same** update step.

```
GPU 0 gradients:  [0.1, 0.3, -0.2]
GPU 1 gradients:  [0.2, 0.1, -0.1]
GPU 2 gradients:  [0.3, 0.2, -0.3]
GPU 3 gradients:  [0.0, 0.4, -0.2]
                  ─────────────────
All-reduce avg:   [0.15, 0.25, -0.2]  ← every GPU gets this
```


### What Happens on Each GPU — Step by Step

1. Load model (full copy) onto GPU
2. Receive a mini-batch (1/N of the global batch, where N = number of GPUs)
3. Forward pass → compute loss on this mini-batch
4. Backward pass → compute gradients on this mini-batch
5. **All-reduce** → average gradients across all GPUs
6. Optimizer step → update weights using averaged gradients
7. Repeat from step 2

Effective batch size = per-GPU batch size × number of GPUs.


## Single-Node vs Multi-Node

### Single-node (1 machine, N GPUs)

```
┌──────────────────────────────────┐
│          Single Machine          │
│                                  │
│  GPU 0 ←──NVLink──→ GPU 1       │
│  GPU 2 ←──NVLink──→ GPU 3       │
│                                  │
│  Communication: NVLink / PCIe    │
│  Bandwidth: 300–900 GB/s         │
│  Latency: microseconds           │
└──────────────────────────────────┘
```

- GPUs talk via **NVLink** or PCIe — very fast
- No network configuration needed
- Launch: `torchrun --nproc_per_node=4`
- **This is the easy path — start here**

### Multi-node (M machines × N GPUs)

```
┌───────────────┐           ┌───────────────┐
│   Node 0      │           │   Node 1      │
│ GPU0 GPU1     │◄─network─►│ GPU0 GPU1     │
│ GPU2 GPU3     │  (NCCL)   │ GPU2 GPU3     │
└───────────────┘           └───────────────┘
```

- GPUs on **different machines** talk over network (Ethernet / InfiniBand)
- Bandwidth: 10–100 GB/s (InfiniBand) or 1–25 Gbps (Ethernet)
- **10–100x slower** than NVLink

### What changes for multi-node

| Concept | Single-node | Multi-node |
|---|---|---|
| **Process groups** | Automatic (shared memory) | Need rendezvous setup |
| **Rendezvous** | Not needed | Master addr + port required |
| **NCCL** | Uses NVLink/PCIe | Uses network (slower) |
| **Bandwidth** | 300–900 GB/s | 10–100 GB/s |
| **Failure blast** | One machine only | Any node can fail |
| **Launch** | `torchrun` | `torchrun` on each node + env vars |

### Rendezvous explained

- All processes need to "find each other" before training starts
- One node is the **master** (usually node 0)
- Master's IP + port = the meeting point
- Every node connects to master to form the process group

```bash
# Node 0 (master)
torchrun --nnodes=2 --node_rank=0 \
         --master_addr=10.0.0.1 --master_port=29500 ...

# Node 1
torchrun --nnodes=2 --node_rank=1 \
         --master_addr=10.0.0.1 --master_port=29500 ...
```

### NCCL (the communication engine)

- NVIDIA Collective Communication Library
- Handles all-reduce, broadcast, gather, scatter
- Automatically picks the fastest transport:
  - Same machine → NVLink / shared memory
  - Different machines → network (TCP / InfiniBand)
- You rarely configure NCCL directly — PyTorch/LlamaFactory handles it

### Network bandwidth sensitivity

All-reduce must move gradient data across the network.

```
Model: 7B params × 4 bytes (fp32) = 28 GB of gradients per step
With fp16: 14 GB per step
With LoRA (0.1% trainable): ~14 MB per step  ← tiny!
```

- Full fine-tuning multi-node: bandwidth is the bottleneck
- **LoRA multi-node: bandwidth is almost irrelevant**
  - WHY: only ~0.1% of params have gradients → tiny all-reduce payload


## DDP vs FSDP (High-Level Tradeoff)

| | DDP | FSDP |
|---|---|---|
| **Model copies** | Full copy on each GPU | Sharded across GPUs |
| **Memory per GPU** | Full model + gradients + optimizer | 1/N of model + gradients + optimizer |
| **Communication** | All-reduce gradients only | All-gather weights + reduce-scatter gradients |
| **Overhead** | Low | Medium (more communication) |
| **When to use** | Model fits on 1 GPU | Model does NOT fit on 1 GPU |

### DDP memory per GPU (7B model)

```
Model:      14 GB
Gradients:  14 GB  (for full FT; ~0 for LoRA)
Optimizer:  28 GB  (for full FT; ~0 for LoRA)
Total:      ~56 GB (full FT) or ~16 GB (LoRA)
```

### FSDP memory per GPU (7B model, 4 GPUs)

```
Model shard:      14 / 4 = 3.5 GB
Gradient shard:   14 / 4 = 3.5 GB
Optimizer shard:  28 / 4 = 7 GB
Total per GPU:    ~14 GB  (full FT — fits on 1 A100!)
```

> Think of it like:
> - DDP = every student carries the full textbook
> - FSDP = students split the textbook; each carries a few chapters
>   and shares when needed


## Where LoRA/QLoRA Fits

LoRA makes distributed training **much cheaper**:

| Concern | Full FT | LoRA |
|---|---|---|
| Trainable params | 7B | ~4M (0.06%) |
| Gradient size | 14 GB | ~8 MB |
| Optimizer state | 28 GB | ~16 MB |
| All-reduce payload | 14 GB | ~8 MB |
| Need FSDP? | Often yes | Almost never |
| Multi-node bottleneck | Network bandwidth | Almost none |

- LoRA + DDP is the sweet spot for most fine-tuning
- FSDP is only needed for full fine-tuning of very large models
- QLoRA adds 4-bit quantization → even lower base memory


## Behind the Scenes: Full Training Step (12 bullets)

1. **Launch**: `torchrun` spawns one process per GPU (each gets a rank)
2. **Init**: Each process joins a NCCL process group (rendezvous for multi-node)
3. **Load model**: Each GPU loads a full model copy (DDP) or a shard (FSDP)
4. **Load data**: DataLoader shards the dataset — each GPU gets different samples
5. **Forward pass**: Each GPU runs forward on its own mini-batch
6. **Loss computation**: Each GPU computes loss independently
7. **Backward pass**: Each GPU computes gradients on its own mini-batch
8. **All-reduce**: NCCL averages gradients across all GPUs
9. **Optimizer step**: Each GPU applies the same averaged gradient update
10. **Checkpoint** (periodic): Rank 0 saves the model; others wait at a barrier
11. **Logging**: Rank 0 logs metrics; others skip to avoid duplicate logs
12. **Repeat** steps 4–11 until training is done


## Common Interview Traps

- **"DDP copies the data to every GPU"** — NO. DDP copies the **model**.
  The **data** is split across GPUs. That's the whole point.

- **"FSDP is always better than DDP"** — NO. FSDP has more communication
  overhead. Use DDP when the model fits; FSDP when it doesn't.

- **"Multi-node is just more GPUs"** — NOT quite. Network bandwidth becomes
  a bottleneck. All-reduce over Ethernet is 10–100x slower than NVLink.

- **"LoRA doesn't benefit from distributed"** — YES it does. You still
  parallelize the **forward pass** (data parallelism = more throughput).

- **"Gradient accumulation replaces distributed"** — NO. Accumulation
  simulates larger batches on one GPU, but doesn't speed up wall-clock time.
  Distributed training gives you actual parallelism.


## TL;DR (Interview Summary)

- DDP = full model copy per GPU, split data, all-reduce gradients — the default
- FSDP = shard model across GPUs — use only when model won't fit on one GPU
- All-reduce averages gradients so all GPUs stay in sync
- Single-node: NVLink (fast, easy); multi-node: network (slower, needs rendezvous)
- LoRA + DDP is the sweet spot — tiny gradient all-reduce (~8 MB vs 14 GB)
- Multi-node needs: `master_addr`, `master_port`, `node_rank`, `nnodes`
- NCCL handles all GPU communication — you rarely touch it directly
- Effective batch size = per_gpu_batch × num_gpus × gradient_accumulation_steps
