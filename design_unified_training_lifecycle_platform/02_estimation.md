# 2. Estimation

> Goal: back-of-envelope numbers to justify resource sizing.
> Keep math 1–2 lines each. State assumptions explicitly.


## Job Volume

| Metric | Estimate | Assumption |
|---|---|---|
| Jobs submitted/day | ~200–500 | 10 teams x 20–50 jobs each |
| Concurrent runs | ~100–200 | Mix of short (eval) and long (fine-tune) |
| Peak burst | ~2x average | End-of-sprint pushes |


## GPU Hours / Day

- **Fine-tune job**: ~2–8 GPU-hours (7B LoRA) to ~24–72 GPU-hours (70B full FT)
- **HPO sweep**: 20 trials x 4 GPU-hours avg = ~80 GPU-hours per sweep
  - With pruning (kill bottom 50% early): ~80 x 0.6 = ~48 GPU-hours
- **RLHF pipeline**: reward model (~4h) + PPO/DPO (~8–16h) = ~12–20 GPU-hours
- **Eval-only**: ~0.5–2 GPU-hours

**Daily GPU budget estimate:**
- ~50 fine-tune jobs x 6h avg = 300 GPU-hours
- ~10 HPO sweeps x 48h avg = 480 GPU-hours
- ~5 RLHF runs x 16h avg = 80 GPU-hours
- ~100 eval jobs x 1h avg = 100 GPU-hours
- **Total: ~960 GPU-hours/day => ~40 GPUs sustained**

WHY this matters: Sizes the GPU pool and sets budget guardrails.


## CPU Hours / Day

- Preprocessing (tokenize, dedup, validate): ~0.5–2 CPU-hours per job
- Metadata/packaging/upload activities: ~minutes each
- ~500 jobs x 1h avg = ~500 CPU-hours/day => ~20 CPU cores sustained

WHY separate: CPU work is cheap; never block GPU queues with it.


## Storage / Day

| Data Type | Per Job (avg) | Daily (500 jobs) |
|---|---|---|
| Datasets (tokenized) | ~1–10 GB | ~2.5 TB |
| Checkpoints | ~2–20 GB | ~5 TB |
| Final models/adapters | ~0.5–5 GB | ~1.25 TB |
| Logs + metrics | ~50 MB | ~25 GB |
| **Daily total** | | **~8–9 TB** |

- Monthly: ~250 TB (before retention policies)
- WHY: Justifies S3 tiered storage + checkpoint TTL policies.


## Preprocessing Throughput

- Tokenization: ~10K–50K examples/sec on CPU (HF tokenizers)
- 10M example dataset: ~200–1000 sec => ~3–17 min
- WHY: Confirms CPU preprocessing doesn't bottleneck the pipeline.


## HPO Explosion Math

- Grid search: 5 params x 4 values each = 4^5 = 1,024 trials (impractical)
  - WHY grid is limited: combinatorial explosion
- Random search: 50–100 trials covers most of the space (Bergstra & Bengio)
- Bayesian (Optuna): 20–50 trials with pruning is usually sufficient
- **Design for: max 100 trials per HPO job, with early stopping**

Worst case: 100 trials x 8 GPU-hours = 800 GPU-hours for one HPO job.
With pruning: ~300–400 GPU-hours. WHY pruning is non-negotiable.


## Temporal Throughput

- ~500 workflow starts/day = ~0.35/sec avg, ~2/sec peak
- Each workflow: 5–15 activities
- Total activity executions: ~5,000/day
- Temporal handles 1,000s of workflows/sec — not a bottleneck

WHY: Confirms Temporal is not the scaling concern; GPUs are.


## TL;DR (Interview Summary)

- ~500 jobs/day, ~100–200 concurrent, ~40 GPUs sustained
- HPO is the cost bomb: 100 trials x 8h = 800 GPU-hours; pruning cuts to ~400
- ~9 TB storage/day; need tiered S3 + checkpoint TTL
- CPU preprocessing is fast (~minutes); keep it off GPU queues
- Temporal throughput is trivially sufficient (~0.35 workflows/sec)
- Budget guardrails must cap per-project GPU-hours to prevent runaway
