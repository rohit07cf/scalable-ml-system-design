# Diagram: FSDP vs DDP


## DDP — Every GPU Has Everything

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    GPU 0     │  │    GPU 1     │  │    GPU 2     │
│              │  │              │  │              │
│ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
│ │ Layer 1  │ │  │ │ Layer 1  │ │  │ │ Layer 1  │ │
│ │ Layer 2  │ │  │ │ Layer 2  │ │  │ │ Layer 2  │ │
│ │ Layer 3  │ │  │ │ Layer 3  │ │  │ │ Layer 3  │ │
│ │ Layer 4  │ │  │ │ Layer 4  │ │  │ │ Layer 4  │ │
│ │ (FULL    │ │  │ │ (FULL    │ │  │ │ (FULL    │ │
│ │  COPY)   │ │  │ │  COPY)   │ │  │ │  COPY)   │ │
│ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │
│              │  │              │  │              │
│ + gradients  │  │ + gradients  │  │ + gradients  │
│ + optimizer  │  │ + optimizer  │  │ + optimizer  │
│              │  │              │  │              │
│ Memory: FULL │  │ Memory: FULL │  │ Memory: FULL │
└──────────────┘  └──────────────┘  └──────────────┘

Sync: all-reduce GRADIENTS only (after backward pass)
```


## FSDP — Each GPU Has a Shard

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    GPU 0     │  │    GPU 1     │  │    GPU 2     │
│              │  │              │  │              │
│ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
│ │ Shard A  │ │  │ │ Shard B  │ │  │ │ Shard C  │ │
│ │ (1/3 of  │ │  │ │ (1/3 of  │ │  │ │ (1/3 of  │ │
│ │  weights │ │  │ │  weights │ │  │ │  weights │ │
│ │  + grads │ │  │ │  + grads │ │  │ │  + grads │ │
│ │  + optim)│ │  │ │  + optim)│ │  │ │  + optim)│ │
│ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │
│              │  │              │  │              │
│ Memory: 1/3  │  │ Memory: 1/3  │  │ Memory: 1/3  │
└──────────────┘  └──────────────┘  └──────────────┘

Sync: all-gather WEIGHTS before forward (reconstruct full layer)
      reduce-scatter GRADIENTS after backward (shard gradients)
      → MORE communication than DDP, but LESS memory per GPU
```


## How FSDP Works (Step by Step)

```
For each layer during forward pass:
  1. All-gather: collect weight shards from all GPUs
     → each GPU temporarily has the full layer
  2. Compute forward for this layer
  3. Discard the gathered weights (free memory)

For each layer during backward pass:
  4. All-gather weights again (need them for backward)
  5. Compute gradients
  6. Reduce-scatter: average and re-shard gradients
  7. Each GPU updates only its shard with its optimizer
```

> Think of it like: a team where each person stores 1/3 of a shared
> document. To read a section, they ask the others to share their parts
> temporarily. After working on it, everyone takes back their piece.


## Side-by-Side Comparison

```
                         DDP                    FSDP
                    ─────────────          ─────────────
Memory per GPU:     FULL model             1/N model
                    + FULL gradients       + 1/N gradients
                    + FULL optimizer       + 1/N optimizer

Communication:      All-reduce             All-gather (forward)
                    (once per step)        + Reduce-scatter (backward)
                                           (per layer, per step)

Overhead:           LOW                    MEDIUM

Best when:          Model FITS             Model DOESN'T FIT
                    on 1 GPU               on 1 GPU
```

### Memory example (7B model, 3 GPUs, full FT)

| | DDP (per GPU) | FSDP (per GPU) |
|---|---|---|
| Weights | 14 GB | 4.7 GB |
| Gradients | 14 GB | 4.7 GB |
| Optimizer | 28 GB | 9.3 GB |
| **Total** | **~56 GB** | **~19 GB** |


## When to Use Which

| Scenario | Use |
|---|---|
| **LoRA fine-tune, any model size** | DDP — adapter is tiny, full copy fits |
| **Full FT, model fits on 1 GPU** | DDP — less communication overhead |
| **Full FT, model doesn't fit on 1 GPU** | FSDP — shard to make it fit |
| **70B full FT, 4× A100 80 GB** | FSDP — 70B doesn't fit on one A100 |

**Key rule**: if DDP works (model fits), use DDP. FSDP only when you need it.


## What to Say in Interviews

- "DDP stores a full model copy per GPU and only syncs gradients.
  FSDP shards the model across GPUs and syncs weights before each
  layer's forward pass. FSDP uses 1/N memory but has more communication."

- "For LoRA fine-tuning, DDP is always the right choice because the
  adapter parameters are tiny — no need to shard."

- "FSDP is the go-to when the model is too large for one GPU's memory
  and you're doing full fine-tuning. It's conceptually similar to
  DeepSpeed ZeRO Stage 3."


## TL;DR (Interview Summary)

- DDP: full model per GPU, all-reduce gradients only — simple, low overhead
- FSDP: shard model across GPUs, all-gather before forward, reduce-scatter after backward
- FSDP uses 1/N memory per GPU but has more communication rounds
- DDP is the default; FSDP only when model doesn't fit on one GPU
- LoRA + DDP is always the right combo — adapters are tiny, no need to shard
- FSDP ≈ DeepSpeed ZeRO Stage 3 (same concept, different implementation)
