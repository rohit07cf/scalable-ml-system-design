# LlamaFactory Distributed — Training & Inference

## What This Module Teaches

- How distributed **training** works (single-node multi-GPU + multi-node)
- How distributed **inference** works (single-node multi-GPU + multi-node)
- The "behind the scenes" of DDP, FSDP, tensor parallelism, and batching
- Practical LlamaFactory configs and launch scripts you can adapt
- Interview-ready explanations for every concept


## Reading Order

### Speed run (10 minutes)

1. `01_distributed_training_concepts.md` — skim DDP vs FSDP section
2. `02_distributed_inference_concepts.md` — skim request lifecycle
3. `03_single_node_multigpu_finetune.md` — the config + command
4. `05_single_node_multigpu_inference.md` — the config + command
5. Read every TL;DR

### Deep pass (30 minutes)

1. All `.md` files in order (01 → 06)
2. Browse `scripts/` — understand the launch patterns
3. Browse `configs/` — understand the YAML keys
4. Skim `python/` — launcher + client
5. Browse `diagrams/` — internalize the ASCII pictures


## Key Interview Talking Points

- DDP = each GPU has a **full copy** of the model; they split data and sync gradients
- FSDP = **shard** the model across GPUs; each GPU holds a slice (saves memory)
- Single-node multi-GPU = `torchrun --nproc_per_node=N`; no network headaches
- Multi-node = add `--nnodes`, `--master_addr`, `--master_port`; NCCL over network
- LoRA + DDP is the sweet spot: small trainable params, full copies are cheap
- Inference parallelism: **tensor parallel** (split layers across GPUs) or **data parallel** (replicas)
- KV cache is the memory bottleneck at inference — determines max concurrent requests
- LlamaFactory wraps all of this behind YAML configs + a simple CLI


## File Index

| # | File | Topic |
|---|---|---|
| 01 | `01_distributed_training_concepts.md` | DDP, FSDP, all-reduce, single vs multi-node |
| 02 | `02_distributed_inference_concepts.md` | Batching, KV cache, tensor parallel, load balancing |
| 03 | `03_single_node_multigpu_finetune.md` | 1 machine, N GPUs — config + command |
| 04 | `04_multi_node_finetune.md` | M machines × N GPUs — rendezvous + scripts |
| 05 | `05_single_node_multigpu_inference.md` | Multi-GPU inference on 1 machine |
| 06 | `06_multi_node_inference.md` | Horizontal scaling across machines |
| — | `scripts/` | Shell launch scripts (train + inference) |
| — | `configs/` | LlamaFactory YAML configs |
| — | `python/` | Launcher + inference client |
| — | `diagrams/` | ASCII diagrams for whiteboard |


## TL;DR (Interview Summary)

- DDP: every GPU has the full model, split data, sync gradients via all-reduce
- FSDP: shard model weights across GPUs — needed when model doesn't fit on one GPU
- LoRA + DDP is the default for fine-tuning — adapters are tiny, full copies are cheap
- Single-node multi-GPU: `torchrun --nproc_per_node=N` — simplest distributed setup
- Multi-node: add rendezvous (master addr/port) + NCCL over network — bandwidth-sensitive
- Inference: tensor parallel for large models, data parallel replicas for throughput
- KV cache dominates inference memory — limits batch size and concurrent requests
- LlamaFactory wraps PyTorch distributed behind YAML + CLI — minimal boilerplate
