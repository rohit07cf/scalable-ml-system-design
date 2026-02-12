# 07 — Key Takeaways


## What Truly Matters in Frontier Training

- **Data quality is the #1 lever.** More data helps, but cleaner, better-mixed
  data helps more. Filtering and deduplication matter as much as scale.

- **Parallelism is always combined.** No real frontier run uses a single
  strategy. It is always DP + TP + PP + ZeRO, tuned to the hardware topology.

- **MoE is the scaling path.** Scaling total parameters while keeping active
  parameters fixed is how labs get more capability without proportional
  compute increase. Most frontier models in 2026 use MoE.

- **Post-training has outsized impact.** Pre-training is 90%+ of the cost,
  but alignment and SFT determine whether the model is actually useful
  and safe. DPO and synthetic data loops are now standard.

- **Infrastructure is the moat.** The ability to build, operate, and maintain
  100K+ GPU clusters reliably for months is what separates frontier labs
  from everyone else. This is an operational challenge, not just an ML one.

- **Checkpointing is survival.** At 10K+ GPUs, hardware failures are not
  rare events — they are constant. Training must be designed for failure:
  frequent checkpoints, fast recovery, redundant storage.

- **The interconnect determines the parallelism partition.** NVLink within
  a node (fast) vs InfiniBand across nodes (slower) is the fundamental
  constraint that shapes how you split TP, PP, and DP.


## What Interviewers Expect You to Know

- The three-phase pipeline: pre-training -> SFT -> alignment
- Why pre-training is expensive (trillions of tokens, months, 10K+ GPUs)
- The difference between DDP, FSDP/ZeRO, TP, PP, and MoE
- How these parallelism strategies are combined in practice
- What hardware frontier labs actually use (H100/B200/GB200, TPUs)
- Where training data comes from and how it is processed
- How preference labeling works (human annotators, Scale AI, RLAIF)
- What a checkpoint contains and why storage is a hard problem
- The dominant frameworks (PyTorch + Megatron/DeepSpeed, JAX + Pathways)


## What Differentiates Infra-Level Understanding from ML-Level Understanding

| ML-level knowledge | Infra-level knowledge |
|---|---|
| "We train with DDP" | "We use DP=64, TP=8, PP=2, ZeRO Stage 3 to fit a 200B model on 1024 H100s" |
| "We use RLHF" | "Preference data is labeled via Scale AI, filtered for agreement, formatted as DPO pairs, trained on a separate smaller cluster" |
| "We checkpoint regularly" | "Checkpoints are 560 GB, saved every 15 min to Lustre, async-replicated to S3, with retention of last 20 + milestones" |
| "We need lots of GPUs" | "100K H100s at 700W each = 70 MW GPU power, ~150 MW facility, liquid-cooled, InfiniBand NDR fat-tree topology" |
| "FlashAttention is fast" | "FlashAttention fuses the attention kernel, eliminates the N x N materialization, gives O(N) memory and 2–4x speedup, mandatory for 128K+ context" |

The difference: **specificity, numbers, and operational awareness.**

In an interview, the person who says "our all-reduce payload for LoRA is ~8 MB
vs ~14 GB for full fine-tuning, so multi-node LoRA barely needs InfiniBand"
sounds fundamentally different from someone who says "LoRA is efficient."


## TL;DR (Interview Summary)

- Data quality > data quantity — filtering and mixing are the real levers
- Parallelism is always combined: DP + TP + PP + ZeRO + MoE in one training run
- MoE scales parameters without proportional compute — the dominant architecture
- Post-training (SFT + alignment) is cheap but high-impact; DPO is the standard
- Infrastructure operations (not just ML) is what separates frontier labs
- Checkpointing = survival; hardware failures are constant at 10K+ GPU scale
- Interviewers want specificity: know the numbers, the hardware, the tradeoffs
