# 01 — PEFT & Fine-Tuning Basics


## What Is Fine-Tuning? (Plain English)

- **Pretrained LLM** = a model that already "knows" language
  - Think of it like: a new hire who speaks English fluently
    but doesn't know your company's tone or policies

- **Fine-tuning** = extra training on YOUR data so it learns YOUR task
  - Think of it like: onboarding — the new hire reads your docs,
    sees examples, and starts writing like your team


### Before vs After (Customer Support Example)

**Prompt:** "Customer says: 'My order is late.' Write a reply."

| | Response |
|---|---|
| **Before fine-tune** | "Your order is late because of shipping delays." |
| **After fine-tune** | "Hi! I'm sorry about the delay. Let me look into your order right away and get back to you within the hour." |

The model learned: be polite, acknowledge, promise action, give timeline.


## Why Full Fine-Tuning Is Expensive

- **Full fine-tuning** = update every single weight in the model
- A 7B parameter model has ~7 billion numbers to update
- That needs:
  - All weights in GPU memory (the model itself)
  - A copy for gradients (same size)
  - Optimizer state (2–3x model size for Adam)
  - **Total: ~4–6x model size in GPU memory**

| Model | Params | Full FT Memory | GPU Cost |
|---|---|---|---|
| 7B | 7 billion | ~56–84 GB | 1–2 A100s |
| 13B | 13 billion | ~104–156 GB | 2–4 A100s |
| 70B | 70 billion | ~560+ GB | 8+ A100s |

> Think of it like: repainting an entire house when you only
> want to change the front door color.


## What Is PEFT?

**PEFT** = Parameter-Efficient Fine-Tuning

- Instead of updating ALL weights, update only a tiny subset
- The base model weights stay **frozen** (unchanged)
- You train a small set of **new parameters** on top

| Approach | What's Updated | % of Params | Memory |
|---|---|---|---|
| Full fine-tuning | Everything | 100% | Very high |
| PEFT (LoRA) | Tiny added matrices | ~0.1–1% | Much lower |

> Think of it like: instead of repainting the whole house,
> you clip a new decoration onto the front door.


## Where Does LoRA Fit?

**LoRA** (Low-Rank Adaptation) is the most popular PEFT method.

- It adds small "adapter" matrices to specific layers
- Only these small matrices get trained
- The original model weights don't change at all
- After training, you can **merge** the adapter back into the model
  or keep it separate

More details in the next file (02).


## Other PEFT Methods (for awareness)

| Method | Idea | When Used |
|---|---|---|
| **LoRA** | Low-rank matrix updates | Most common, best cost/quality |
| **QLoRA** | LoRA + quantized base model | Even cheaper, almost same quality |
| **Prefix Tuning** | Learn soft prompt tokens | Lighter than LoRA, less flexible |
| **Adapters (Houlsby)** | Small layers inserted into model | Older approach, LoRA mostly replaced it |

For interviews: know LoRA + QLoRA well. Mention others exist.


## Interview Answer: "What is PEFT?"

> "PEFT means we freeze the base model and only train a small set of
> new parameters — typically less than 1% of the total. The most common
> method is LoRA, which adds small low-rank matrices to attention layers.
> This cuts GPU memory by 5–10x compared to full fine-tuning while
> getting nearly the same quality. QLoRA goes further by quantizing the
> base model to 4-bit, so you can fine-tune a 7B model on a single
> consumer GPU."


## TL;DR (Interview Summary)

- Fine-tuning = extra training on your data so the LLM learns your task/tone
- Full fine-tuning updates ALL weights — needs 4–6x model size in GPU memory
- PEFT freezes the base model, trains only ~0.1–1% new parameters
- LoRA is the most popular PEFT method — adds small matrices to attention layers
- QLoRA = LoRA + 4-bit quantized base — cheapest option, nearly same quality
- Result: fine-tune a 7B model on 1 GPU instead of 2–4
- After training, adapter can be merged into base or kept separate
- In interviews: lead with "freeze base, train small adapter" — that's the core idea
