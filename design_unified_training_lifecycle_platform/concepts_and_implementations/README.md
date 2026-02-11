# Concepts & Implementations — PEFT, Adapters, RLHF

## What This Folder Teaches

> You already have the system design (../01–07 files).
> This folder fills the gap: **"What actually happens inside those
> training boxes?"**
>
> After reading this you can explain — in an interview — how LoRA
> fine-tuning works, what an adapter is, how it merges into a base
> model, what RLHF does, and why DPO is simpler than PPO.
>
> Everything uses one running example:
> **"Customer Support Reply Model"** — adapt a generic LLM to produce
> polite, company-style support replies, then align it with human
> preferences.


## Reading Order

### Speed run (10 minutes)

1. `01_peft_finetuning_basics.md` — what fine-tuning is, why PEFT exists
2. `02_lora_qlora_full_finetune.md` — skim the comparison table
3. `05_rlhf_basics.md` — what RLHF is, PPO vs DPO at a glance
4. Read the TL;DR of every other file

### Deep pass (30 minutes)

1. All `.md` files in order (01 → 08)
2. Skim `04_minimal_peft_example.py` — understand the flow
3. Skim `09_rlhf_minimal_reference_code.py` — understand the flow
4. Browse `diagrams/` — internalize the ASCII pictures


## What You Should Be Able to Explain in Interviews

- What fine-tuning is and why full FT is expensive
- What LoRA does and why it saves memory
- QLoRA = quantized base + LoRA adapters (best cost/quality)
- What an "adapter" is and how merging works
- What RLHF solves (alignment, preference shaping)
- PPO: needs a reward model, trains via RL loop
- DPO: skips the reward model, trains directly on preference pairs
- When to pick PPO vs DPO
- What preference data looks like and how to collect it


## File Index

| # | File | Topic |
|---|---|---|
| 01 | `01_peft_finetuning_basics.md` | Fine-tuning & PEFT overview |
| 02 | `02_lora_qlora_full_finetune.md` | LoRA vs QLoRA vs Full FT |
| 03 | `03_adapters_and_merging.md` | Adapters, attaching, merging |
| 04 | `04_minimal_peft_example.py` | Runnable PEFT LoRA code |
| 05 | `05_rlhf_basics.md` | RLHF overview |
| 06 | `06_ppo_explained_with_toy_example.md` | PPO deep dive |
| 07 | `07_dpo_explained_with_toy_example.md` | DPO deep dive |
| 08 | `08_preference_data_pipeline.md` | Preference data pipeline |
| 09 | `09_rlhf_minimal_reference_code.py` | RLHF reference code |
| — | `diagrams/` | ASCII diagrams for whiteboard |


## TL;DR (Interview Summary)

- Fine-tuning = take a pretrained LLM, train it further on your task data
- PEFT = train only a small piece, not all weights — saves 90%+ memory
- LoRA = inject tiny low-rank matrices; QLoRA = quantize base + LoRA (cheapest)
- Adapter = the small trained piece; it can be saved, swapped, or merged
- RLHF = align model outputs with human preferences (not just task accuracy)
- PPO = full RL loop with reward model — flexible but complex and expensive
- DPO = skip reward model, optimize on preference pairs directly — simpler, cheaper
- Preference data = (prompt, chosen_response, rejected_response) triplets
