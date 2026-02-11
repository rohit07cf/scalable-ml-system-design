# 03 — Adapters & Merging


## What Is an "Adapter"?

- **Adapter** = the small set of weights you trained during PEFT/LoRA
- It's NOT a separate model — it's a modification that sits on top of a base model
- Saved as a tiny file (~10–50 MB) separate from the base model (~14 GB for 7B)

> Think of it like: the base model is a **camera body**.
> The adapter is a **clip-on lens**.
> The lens changes what the camera sees, but it's not a camera by itself.

### What's inside an adapter file?

- The low-rank matrices A and B for each targeted layer
- A config file saying which layers were adapted, what rank was used
- That's it — no copy of the base model


## How the Adapter Attaches During Training

```
              Base Model (frozen)
              ┌──────────────────┐
   input ───> │  Attention Layer  │ ──> original output
              │   W (frozen)      │
              └──────────────────┘
                       +
              ┌──────────────────┐
              │  LoRA Adapter     │ ──> small correction
              │   A · B (trained) │
              └──────────────────┘
                       =
              final output = original + correction
```

- During training, both paths run in parallel
- Only the adapter path (A, B) gets gradient updates
- The base model W is never modified

### At inference time (adapter NOT merged)

- Same two-path computation
- Slightly slower: two matrix multiplications instead of one
- But you can **hot-swap adapters** without reloading the base model

> Think of it like: the clip-on lens adds a tiny bit of processing time,
> but you can pop it off and clip on a different one instantly.


## Merging: Combining Adapter Into Base

### What merging does

```python
# Conceptual merge — that's literally it
merged_weight = base_weight + (lora_A @ lora_B) * scaling_factor
```

- Take each adapted layer's base weight W
- Add the LoRA correction (A * B * scale)
- Result: a single weight matrix that includes the adaptation
- Save as a new, full-size model

### Why merge?

| Benefit | Explanation |
|---|---|
| **Faster inference** | One matrix multiply instead of two — no adapter overhead |
| **Simpler deployment** | Ship one model file, no adapter loading logic |
| **Framework compatibility** | Merged model works with any serving framework |

### When NOT to merge

| Situation | Why keep separate |
|---|---|
| **Multi-adapter serving** | Same base + different adapters per customer/use-case |
| **A/B testing adapters** | Swap adapters without redeploying the base |
| **Storage efficiency** | 10 adapters (500 MB total) vs 10 merged models (140 GB total) |
| **Experimentation** | Train many adapters, merge only the winner |

> Think of it like:
> - **Merged** = you glued the clip-on lens permanently onto the camera.
>   Faster, simpler, but now it's a fixed-purpose camera.
> - **Separate** = keep the lens detachable.
>   Slightly slower, but you can swap lenses anytime.


## Merge Pseudocode

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

# 1. Load base model
base_model = AutoModelForCausalLM.from_pretrained("base-model-name")

# 2. Load adapter on top
model_with_adapter = PeftModel.from_pretrained(base_model, "path/to/adapter")

# 3. Merge adapter weights into base weights
merged_model = model_with_adapter.merge_and_unload()
#   merge_and_unload() does:
#     for each adapted layer:
#       W_new = W_base + (A @ B) * scaling
#     then removes the adapter hooks

# 4. Save as a standalone model
merged_model.save_pretrained("path/to/merged-model")
```

### What `merge_and_unload()` does step by step

1. For each layer that has a LoRA adapter:
   - Compute the correction: `delta = A @ B * scaling_factor`
   - Add it to the base weight: `W = W + delta`
2. Remove all LoRA hooks from the model
3. Return a clean model that looks like it was never adapted

Result: a normal model file, same size as the original, but with your fine-tuning baked in.


## Runtime Tradeoffs Summary

| | Adapter (separate) | Merged |
|---|---|---|
| **Inference speed** | Slightly slower (~5–10%) | Full speed |
| **Memory at inference** | Base + adapter overhead | Same as base |
| **Swap adapters** | Yes (hot-swap) | No (reload entire model) |
| **Storage (10 variants)** | 1 base + 10 adapters (~500 MB) | 10 full models (~140 GB) |
| **Deployment complexity** | Need adapter-aware serving | Standard serving |
| **Best for** | Multi-tenant, experimentation | Single-purpose production |


## Common Mistakes

- Thinking you need the adapter file at inference after merging
  — no, the merge bakes everything in. Adapter file is only for re-creating.

- Forgetting to save the adapter separately before merging
  — always save the adapter first, then merge. You may want to un-merge later.

- Merging QLoRA adapters without dequantizing first
  — you must convert the 4-bit base back to 16-bit before merging.
  The PEFT library handles this, but it's a gotcha if doing it manually.


## Interview Answer: "What are adapters and when do you merge?"

> "An adapter is the small set of trained LoRA weights — typically tens of
> megabytes. During training and inference, it runs alongside the frozen
> base model, adding a small correction to each adapted layer. You can
> merge the adapter into the base model for faster inference and simpler
> deployment, but you lose the ability to hot-swap adapters. We keep
> adapters separate when serving multiple variants from one base model,
> and merge when deploying a single production model."


## TL;DR (Interview Summary)

- Adapter = the tiny LoRA weights (~10–50 MB), not a full model
- It clips onto a frozen base model — adds corrections, doesn't replace
- Separate serving: slightly slower, but hot-swappable (great for multi-tenant)
- Merged serving: full speed, simpler deploy, but locked to one variant
- Merge is literally: `W_new = W_base + A @ B * scale` for each layer
- Always save the adapter BEFORE merging — you may need to un-merge later
- QLoRA merge requires dequantizing the base first
- Default: keep adapters separate during experimentation, merge the winner for production
