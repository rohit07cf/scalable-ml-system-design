# Phase 2 — Estimation (Back-of-Envelope)

## Assumptions

| Parameter | Value | Rationale |
|---|---|---|
| Enterprise teams | ~50 teams | Large enterprise, single org |
| Active agent configs | ~200 | ~4 configs/team avg |
| Runs per day | ~10,000 | ~200 runs/team/day across all configs |
| Peak-to-average ratio | 3x | Business-hours spike (9am–5pm) |

---

## QPS

- **Average QPS** = 10,000 runs/day ÷ 86,400 sec ≈ **0.12 runs/sec**
- **Peak QPS** = 0.12 × 3 ≈ **0.35 runs/sec** (~1 run every 3 seconds)
- **WHY this is low**: Each run is long-lived (seconds to minutes), so the bottleneck is *concurrent runs*, not request rate

---

## Concurrent Runs

- Average run duration: **30 seconds** (multi-step with LLM + tool calls)
- **Peak concurrent runs** = 0.35 runs/sec × 30 sec = **~10–12 concurrent runs**
- Burst scenario (batch triggers): up to **50 concurrent runs**
- **WHY**: Sizing workers and Temporal task queues around concurrency, not QPS

---

## Steps Per Run

- Average steps per run: **6 steps** (1 supervisor triage + 3–4 specialist steps + 1 verifier)
- Max step limit: **25 steps** (hard cap)
- Total steps/day: 10,000 × 6 = **60,000 steps/day**
- **WHY**: Each step = 1 Temporal activity = 1 LLM call + possible tool call

---

## Tool Calls Per Step

- ~60% of steps include a tool call → **0.6 tool calls/step**
- Total tool calls/day: 60,000 × 0.6 = **36,000 tool calls/day**
- Average tool call latency: **2 seconds** (API calls, DB queries)
- **WHY**: Tools are the main source of latency variance; need timeout + retry budgets

---

## Stream Events Per Second

- Events per step: ~4 (step_start, tool_call_start, tool_call_result, step_end)
- Events per run: 6 steps × 4 events = **~24 events/run**
- Peak concurrent streams: ~12 runs × 1 client each = **~12 SSE connections**
- Peak events/sec: 12 runs × (24 events ÷ 30 sec) ≈ **~10 events/sec** globally
- **WHY**: Modest event throughput; a single Redis pub/sub node handles this easily

---

## Token Usage Per Day

- Average tokens per LLM call: **~2,000 input + ~500 output = 2,500 tokens**
- LLM calls/day: 60,000 steps (each step has 1 LLM call)
- **Total tokens/day**: 60,000 × 2,500 = **150M tokens/day**
- At $3/M input + $15/M output tokens (GPT-4 class):
  - Input cost: 60K × 2,000 × $3/M = **$360/day**
  - Output cost: 60K × 500 × $15/M = **$450/day**
  - **Total: ~$810/day ≈ $24K/month**
- **WHY**: Token budget enforcement per run is critical to control costs; one runaway loop could burn $50+ in minutes

---

## Storage

- Step ledger row size: ~2 KB (metadata) + ~4 KB (LLM context snapshot) ≈ **6 KB/step**
- Daily storage: 60,000 × 6 KB = **360 MB/day**
- 90-day retention: **~32 GB** — fits comfortably in a single PostgreSQL instance
- **WHY**: Storage is not the bottleneck; audit retention policy drives the number, not capacity

---

## Summary Table

| Metric | Value |
|---|---|
| Runs/day | ~10,000 |
| Peak QPS (new runs) | ~0.35/sec |
| Peak concurrent runs | 10–50 |
| Steps/day | ~60,000 |
| Tool calls/day | ~36,000 |
| Stream events/sec (peak) | ~10 |
| Tokens/day | ~150M |
| Estimated LLM cost/month | ~$24K |
| Storage (90-day) | ~32 GB |

---

## TL;DR (Interview Summary)
- **Low QPS (~0.35/sec)** but each run is long-lived → size for **concurrency** (10–50 runs), not throughput
- **6 steps/run average**, 25 step hard cap → ~60K steps/day
- **~150M tokens/day** ≈ **$24K/month** LLM cost → token budgets per run are essential
- **~10 SSE events/sec** globally → single Redis pub/sub handles streaming easily
- **~32 GB** over 90 days → PostgreSQL handles storage without sharding
- Bottleneck is **LLM call latency** (seconds per step), not data volume or request rate
