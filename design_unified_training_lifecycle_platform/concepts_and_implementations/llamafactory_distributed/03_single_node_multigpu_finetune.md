# 03 — Single-Node Multi-GPU Fine-Tuning (LlamaFactory)


## The Simplest Path

- **1 machine, N GPUs** (e.g., 4× A100 on one server)
- No network configuration, no rendezvous headaches
- LlamaFactory handles DDP via `torchrun` under the hood
- This is where you start 95% of the time


## Minimal LoRA Config

See `configs/finetune_lora_single_node.yaml` for the full file.

Key settings:

```yaml
### Model
model_name_or_path: meta-llama/Llama-3.1-8B-Instruct

### Method
stage: sft                     # supervised fine-tuning
finetuning_type: lora          # LoRA (not full FT)
lora_rank: 8                   # rank — controls adapter size
lora_target: all               # apply LoRA to all linear layers

### Dataset
dataset: my_support_data       # your dataset name in dataset_info.json
template: llama3               # chat template matching the base model

### Output
output_dir: ./output/lora_sft

### Training
per_device_train_batch_size: 4
gradient_accumulation_steps: 2 # effective batch = 4 × 2 × num_gpus
num_train_epochs: 3
learning_rate: 2.0e-4
bf16: true                     # bfloat16 — better than fp16 on A100
```


## Launch Command

```bash
# 4 GPUs on one machine
llamafactory-cli train configs/finetune_lora_single_node.yaml
```

LlamaFactory auto-detects multiple GPUs and wraps with `torchrun`.

If you want explicit control:

```bash
torchrun --nproc_per_node=4 \
    -m llamafactory.train \
    configs/finetune_lora_single_node.yaml
```

> Flags may vary by LlamaFactory version.


## Key Settings Explained

### Gradient accumulation

```
effective_batch = per_device_batch × gradient_accumulation × num_gpus
               = 4              × 2                      × 4
               = 32
```

- WHY: larger effective batch → more stable training
- Without enough GPU memory for big batches, accumulate over multiple steps

### bf16 / fp16

- **bf16** (bfloat16): preferred on A100/H100 — wider range, fewer overflow issues
- **fp16** (float16): works on older GPUs (V100, T4) — needs loss scaling

| GPU | Use |
|---|---|
| A100 / H100 | `bf16: true` |
| V100 / T4 | `fp16: true` |

### Checkpointing

```yaml
save_strategy: steps
save_steps: 500              # save every 500 steps
save_total_limit: 3          # keep only the 3 most recent
```

- WHY: if training crashes, you resume from last checkpoint
- `save_total_limit` prevents filling disk with hundreds of checkpoints


## What Happens Behind the Scenes

1. `llamafactory-cli` reads the YAML config
2. Detects N available GPUs via `CUDA_VISIBLE_DEVICES` or auto-detection
3. Spawns N processes with `torchrun --nproc_per_node=N`
4. Each process:
   - Loads the base model (full copy — DDP)
   - Applies LoRA config (freezes base, creates adapter matrices)
   - Gets a unique data shard from the DataLoader
5. Each step:
   - Forward pass on local mini-batch
   - Backward pass → gradients (only for LoRA params, ~8 MB)
   - **All-reduce**: NCCL averages LoRA gradients across GPUs
   - Optimizer updates LoRA params
6. Rank 0 handles:
   - Logging (other ranks stay silent)
   - Checkpointing (saves adapter weights to `output_dir`)
7. Training ends → adapter saved → base model untouched


## Common Traps

- Setting `per_device_train_batch_size` too high → OOM
  - Start low (2 or 4), increase until memory is ~80% used

- Forgetting `gradient_accumulation_steps` → tiny effective batch
  - Rule of thumb: effective batch of 16–64 is a good range

- Using `fp16` on A100 → works but `bf16` is better (no loss scaling needed)

- Not setting `save_total_limit` → hundreds of checkpoints fill disk

- Thinking each GPU needs separate config → NO.
  One config, one command. DDP handles the rest.


## TL;DR (Interview Summary)

- Single-node multi-GPU: the simplest distributed setup — start here
- LlamaFactory auto-detects GPUs and wraps `torchrun` for you
- Each GPU gets a full model copy (DDP) + different data slice
- LoRA gradients are tiny (~8 MB) → all-reduce is nearly free
- Effective batch = per_device × gradient_accumulation × num_gpus
- Use `bf16` on A100/H100, `fp16` on older GPUs
- Set `save_total_limit` to avoid filling disk with checkpoints
- One config file, one command — DDP complexity is hidden
