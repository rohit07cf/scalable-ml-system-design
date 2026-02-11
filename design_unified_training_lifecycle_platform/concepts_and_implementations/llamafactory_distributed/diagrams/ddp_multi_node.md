# Diagram: DDP Across Multiple Nodes


## ASCII Diagram

```
     Node 0 (master)                          Node 1
┌───────────────────────────┐         ┌───────────────────────────┐
│  ┌───────┐   ┌───────┐   │         │  ┌───────┐   ┌───────┐   │
│  │ GPU 0 │   │ GPU 1 │   │         │  │ GPU 2 │   │ GPU 3 │   │
│  │ rank=0│   │ rank=1│   │         │  │ rank=2│   │ rank=3│   │
│  │ Full  │   │ Full  │   │         │  │ Full  │   │ Full  │   │
│  │ Model │   │ Model │   │         │  │ Model │   │ Model │   │
│  │ Batch │   │ Batch │   │         │  │ Batch │   │ Batch │   │
│  │ 1/4   │   │ 2/4   │   │         │  │ 3/4   │   │ 4/4   │   │
│  └───┬───┘   └───┬───┘   │         │  └───┬───┘   └───┬───┘   │
│      │           │        │         │      │           │        │
│      └─────┬─────┘        │         │      └─────┬─────┘        │
│            │ NVLink        │         │            │ NVLink        │
│            │ (fast)        │         │            │ (fast)        │
└────────────┼──────────────┘         └────────────┼──────────────┘
             │                                     │
             │         ┌─────────────────┐         │
             └────────>│   ALL-REDUCE    │<────────┘
                       │  across nodes   │
                       │  via NETWORK    │
                       │  (NCCL over     │
                       │   Ethernet or   │
                       │   InfiniBand)   │
                       │  ~10–100 GB/s   │
                       └─────────────────┘
                               │
                               ▼
                    All 4 GPUs get the same
                    averaged gradients
```


## Plain-English Explanation

1. Multiple machines, each with N GPUs
2. Each GPU still gets a **full model copy** (same as single-node DDP)
3. Data is split across ALL GPUs globally (not just within one node)
4. Forward + backward passes are independent per GPU
5. All-reduce now happens in TWO phases:
   - **Intra-node**: GPUs on the same machine sync via NVLink (fast)
   - **Inter-node**: nodes sync over the network (slower)
6. NCCL is smart: it does intra-node first, then sends one aggregated
   result across the network (reduces cross-network traffic)
7. Network bandwidth is the bottleneck — especially for full fine-tuning

### Rendezvous (how they find each other)

```
Before training starts:

  Node 0 says: "I'm the master at 10.0.0.1:29500, I have 2 GPUs"
  Node 1 says: "I'm connecting to 10.0.0.1:29500, I have 2 GPUs"

  → Process group formed: world_size=4, ranks=[0,1,2,3]
  → Training can begin
```


## Key Difference from Single-Node

| | Single-node | Multi-node |
|---|---|---|
| All-reduce speed | NVLink: 300–900 GB/s | Network: 10–100 GB/s |
| Setup | One command | Env vars on each node |
| Failure | One machine | Any node can die |
| LoRA impact | Fast either way | Network barely matters (~8 MB) |
| Full FT impact | Fast | Network is the bottleneck |


## What to Say in Interviews

- "Multi-node DDP is the same as single-node — full model copies, split
  data, all-reduce gradients — but the all-reduce now goes over the
  network, which is 10–100x slower than NVLink."

- "NCCL optimizes this by doing intra-node reduce first over NVLink,
  then only sending one aggregated result per node across the network.
  This minimizes cross-network traffic."

- "For LoRA fine-tuning, the all-reduce payload is ~8 MB, so even a slow
  network barely matters. Multi-node LoRA scales almost linearly."


## TL;DR (Interview Summary)

- Same as single-node DDP, but all-reduce goes over the network (slower)
- NCCL optimizes: intra-node first (NVLink), then inter-node (network)
- Network bandwidth is the bottleneck for full FT (~14 GB gradients)
- LoRA multi-node: all-reduce is ~8 MB — network barely matters
- Needs rendezvous: `master_addr`, `master_port`, `node_rank`, `nnodes`
- If any node dies, all nodes must restart (DDP requires full group)
