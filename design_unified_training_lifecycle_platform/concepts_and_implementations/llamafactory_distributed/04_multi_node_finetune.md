# 04 — Multi-Node Fine-Tuning (LlamaFactory)


## When You Need Multi-Node

- Model too large for one machine's GPUs (even with FSDP sharding)
- Need more throughput: more GPUs = larger effective batch = faster epochs
- Enterprise clusters with shared pools across machines

Most LoRA jobs **don't** need multi-node (single-node is enough).
Full fine-tuning of 70B+ models often does.


## What Changes vs Single-Node

| Concern | Single-node | Multi-node |
|---|---|---|
| GPU communication | NVLink (fast) | Network + NVLink |
| Setup | One command | Env vars on every node |
| Rendezvous | Automatic | Must set master_addr + port |
| Failure | One machine | Any node can die |
| Bandwidth needs | Low (NVLink) | High (network) |


## Environment Variables Needed

Every node must have these set:

```bash
MASTER_ADDR=10.0.0.1    # IP of node 0 (the "master")
MASTER_PORT=29500        # any free port — all nodes must agree
NNODES=2                 # total number of machines
NODE_RANK=0              # 0 for master, 1 for second node, etc.
NPROC_PER_NODE=4         # GPUs per machine
```


## Rendezvous / Master Concept

```
  Node 0 (master)               Node 1
  MASTER_ADDR=10.0.0.1          MASTER_ADDR=10.0.0.1
  NODE_RANK=0                   NODE_RANK=1
       │                             │
       └──────── meet here ──────────┘
                (port 29500)

  "Hey, I'm rank 0 with 4 GPUs"   "Hey, I'm rank 1 with 4 GPUs"
  → world_size = 8 (total GPUs)
  → ranks: 0,1,2,3 on node 0 and 4,5,6,7 on node 1
```

- Master doesn't do more work — it's just the meeting point
- If master dies, the whole job fails (it's the rendezvous anchor)
- In Kubernetes: a headless service or the pod-0 IP serves as master


## Launch Script (Per Node)

```bash
# Run this on EACH node (change NODE_RANK per node)

torchrun \
    --nnodes=2 \
    --nproc_per_node=4 \
    --node_rank=${NODE_RANK} \
    --master_addr=${MASTER_ADDR} \
    --master_port=${MASTER_PORT} \
    -m llamafactory.train \
    configs/finetune_lora_multi_node.yaml
```

See `scripts/finetune_multi_node.sh` for a full script.

> Flags may vary by LlamaFactory version.


## K8s Mental Model

In Kubernetes, multi-node training typically uses a **Job** or
**PyTorchJob** (Kubeflow):

```
┌───────────────────────────────────────────┐
│            Kubernetes Cluster             │
│                                           │
│  ┌─────────────┐    ┌─────────────┐      │
│  │  Worker Pod 0│    │  Worker Pod 1│      │
│  │  (master)    │    │              │      │
│  │  NODE_RANK=0 │◄──►│  NODE_RANK=1 │      │
│  │  4 GPUs      │    │  4 GPUs      │      │
│  └─────────────┘    └─────────────┘      │
│                                           │
│  PyTorchJob sets env vars automatically:  │
│    MASTER_ADDR = pod-0 service IP         │
│    MASTER_PORT = 29500                    │
│    NODE_RANK   = pod index                │
└───────────────────────────────────────────┘
```

Key points:
- **One worker pod per node** — each pod gets scheduled to a GPU node
- PyTorchJob operator sets all env vars automatically
- Pods communicate via cluster network (ideally with high-bandwidth CNI)
- Headless service gives pod-0 a stable DNS name for `MASTER_ADDR`


## Config Differences (vs Single-Node)

The YAML config is **almost identical** to single-node.
Multi-node setup is entirely in the **launch command + env vars**.

One thing to adjust:

```yaml
# Multi-node may want deepspeed for better scaling
deepspeed: ds_z2_config.json   # ZeRO Stage 2 (optional)
```

DeepSpeed ZeRO Stage 2 = similar to FSDP — shards optimizer + gradients across nodes.
Useful for full fine-tuning multi-node. Not needed for LoRA (already lightweight).


## Failure / Restart Notes

### Spot / preemption (any node dies)

- **All nodes must restart** — DDP/FSDP requires the full process group
- Resume from last checkpoint (saved to shared storage like S3/NFS)
- Temporal or PyTorchJob operator handles restart logic

### Checkpoint strategy for multi-node

```yaml
save_strategy: steps
save_steps: 200            # more frequent saves (spot risk)
save_total_limit: 3
```

- Save to **shared storage** (S3, NFS) — not local disk
  - WHY: if node dies, local disk is lost
- On restart: load latest checkpoint, rebuild process group, continue

### Network partition

- If one node loses network → NCCL timeout → all processes hang
- NCCL_TIMEOUT (default ~30 min) controls how long before failing
- Set it lower in production:

```bash
export NCCL_TIMEOUT=300   # fail after 5 min, not 30
```


## Common Traps

- **Forgetting to set env vars on all nodes** → rendezvous hangs forever

- **Different LlamaFactory / PyTorch versions across nodes**
  → subtle NCCL errors. Pin versions in Docker image.

- **Saving checkpoints to local disk** → lost when the node dies.
  Always use shared storage.

- **NCCL_TIMEOUT too long** → hang for 30 minutes before detecting a dead node

- **Not testing single-node first** → debug on 1 machine, then scale out


## TL;DR (Interview Summary)

- Multi-node adds: `MASTER_ADDR`, `MASTER_PORT`, `NNODES`, `NODE_RANK` env vars
- Rendezvous = all processes meet at master's IP:port to form a process group
- NCCL handles cross-node communication — needs fast network (InfiniBand ideal)
- The training YAML config is nearly identical to single-node
- In K8s: PyTorchJob operator sets env vars; one worker pod per node
- Checkpoints must go to shared storage (S3/NFS) — local disk is lost on node failure
- If any node dies, all nodes must restart and resume from checkpoint
- LoRA multi-node: all-reduce is tiny (~8 MB) — network is barely a bottleneck
