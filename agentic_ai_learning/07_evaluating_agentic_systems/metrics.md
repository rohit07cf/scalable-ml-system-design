# Evaluation Metrics

## What It Is

- **Metrics** = quantitative measures of how well your agent system performs
- Agent metrics go beyond traditional ML metrics — they measure task completion, not just model accuracy
- Six categories: success, efficiency, cost, safety, latency, quality
- Metrics drive improvement — what you don't measure, you can't improve

## Why It Matters (Interview Framing)

> "Every system design interview ends with 'How would you evaluate this?' Having a crisp answer with specific metrics, thresholds, and measurement methods shows you think about production systems, not just demos."

---

## The Six Metric Categories

```
┌─────────────────────────────────────────────────────┐
│              AGENT EVALUATION METRICS                 │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ SUCCESS  │ │EFFICIENCY│ │   COST   │           │
│  │ Rate     │ │ Steps,   │ │ $/run,   │           │
│  │          │ │ tokens   │ │ $/task   │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  SAFETY  │ │ LATENCY  │ │ QUALITY  │           │
│  │Violations│ │ P50, P99 │ │ Halluc., │           │
│  │          │ │ TTFT     │ │ relevance│           │
│  └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────┘
```

---

## Metric Details

### 1. Task Success Rate

**Definition:** Percentage of agent runs that successfully achieve the stated goal.

```
Success Rate = (Successful Runs / Total Runs) × 100
```

| Measurement Type | How | When |
|---|---|---|
| **Binary** | Did the agent complete the task? (yes/no) | Simple tasks |
| **Partial** | What % of subtasks were completed? | Complex multi-step tasks |
| **Graded** | Quality score 0-1 for each output | Quality-sensitive tasks |

**Targets:**
- Prototype: > 70%
- Production (internal): > 85%
- Production (customer-facing): > 95%

---

### 2. Efficiency

**Definition:** How many resources (steps, tokens, tool calls) the agent uses to complete a task.

| Metric | Formula | Why It Matters |
|---|---|---|
| **Steps per task** | Avg reasoning loop iterations | More steps = more cost + latency |
| **Tokens per task** | Total input + output tokens | Direct cost driver |
| **Tool calls per task** | Number of tool invocations | External API cost + latency |
| **Redundant actions** | Tool calls that don't advance the goal | Waste indicator |

```
Ideal efficiency profile:
  Simple task:  2-3 steps, 1-2 tool calls, < 5K tokens
  Medium task:  5-8 steps, 3-5 tool calls, < 20K tokens
  Complex task: 10-15 steps, 5-10 tool calls, < 50K tokens
```

⚠️ **If efficiency is trending up (more steps for same task type), something is degrading.**

---

### 3. Cost

**Definition:** Total monetary cost per agent run.

```
Cost = Σ (tokens × price_per_token) + Σ (tool_call_costs) + infra_cost_per_run
```

| Cost Component | Typical Range | Optimization |
|---|---|---|
| **LLM tokens** | $0.01-$2.00 per run | Model routing, caching |
| **Tool calls** | $0.001-$0.10 per call | Caching, batching |
| **Infrastructure** | $0.001-$0.01 per run | Efficient scaling |

**Cost tracking:**
```python
cost_tracker = {
    "llm_input_tokens": 12500,
    "llm_output_tokens": 3200,
    "llm_cost": 0.042,
    "tool_calls": 5,
    "tool_cost": 0.003,
    "total_cost": 0.045,
    "cost_per_subtask": 0.009
}
```

---

### 4. Safety Violations

**Definition:** Instances where the agent produces harmful, incorrect, or policy-violating output.

| Violation Type | Severity | Measurement |
|---|---|---|
| **PII leakage** | Critical | Automated PII detection on outputs |
| **Unauthorized actions** | Critical | Audit log analysis |
| **Policy violations** | High | Rule-based + LLM-based checks |
| **Harmful content** | High | Content safety classifier |
| **Hallucinated actions** | Medium | Action validation against allowed set |

**Target:** 0% for critical violations. < 1% for medium.

---

### 5. Latency

**Definition:** Time from request to response.

| Metric | What It Measures | Typical Target |
|---|---|---|
| **P50 latency** | Median response time | < 10s |
| **P99 latency** | Worst-case response time | < 60s |
| **TTFT** | Time to first token (streaming) | < 2s |
| **Step latency** | Time per reasoning step | < 3s |
| **Tool latency** | Time per tool call | < 5s |

```
Latency breakdown for typical agent run:
  Planning:     500ms  ████
  Step 1 (LLM): 200ms  ██
  Step 1 (Tool): 800ms  ████████
  Step 2 (LLM): 200ms  ██
  Step 2 (Tool): 500ms  █████
  Step 3 (LLM): 300ms  ███
  Synthesis:    400ms  ████
  ─────────────────────
  Total:       2900ms
```

---

### 6. Quality (Hallucination Rate)

**Definition:** Percentage of agent outputs containing hallucinated or unfaithful content.

| Quality Metric | What It Measures |
|---|---|
| **Faithfulness** | Does the output align with the retrieved context? |
| **Relevance** | Does the output address the user's question? |
| **Hallucination rate** | % of outputs with made-up facts |
| **Completeness** | Does the output address ALL parts of the request? |
| **Coherence** | Is the output logically consistent? |

**Measurement approaches:**
- **LLM-as-judge:** Use a separate LLM to score quality
- **Human evaluation:** Gold standard but expensive
- **Automated metrics:** Ragas, TruLens, DeepEval
- **Ground truth:** Compare against known-correct answers

---

## Metrics Dashboard

```
┌─────────────────────────────────────────────────┐
│  AGENT SYSTEM HEALTH DASHBOARD                   │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ KEY METRICS (Last 24h)                  │    │
│  │                                         │    │
│  │ Success Rate:  94.2% ✅ (target: >90%)  │    │
│  │ Avg Cost:      $0.045 ✅ (target: <$0.10)│   │
│  │ P50 Latency:   8.2s  ✅ (target: <10s)  │    │
│  │ P99 Latency:   45s   ⚠️ (target: <60s)  │    │
│  │ Halluc. Rate:  2.1%  ✅ (target: <5%)   │    │
│  │ Safety Viols:  0     ✅ (target: 0)      │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ TRENDS (7-day rolling)                  │    │
│  │                                         │    │
│  │ Success: ━━━━━━━━━━━━▶ stable           │    │
│  │ Cost:    ━━━━━━━╲━━━━▶ decreasing ✅     │    │
│  │ Latency: ━━━━╱━━━━━━▶ increasing ⚠️     │    │
│  │ Steps:   ━━━━━━━━━━━━▶ stable           │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

---

## Interview Questions They Will Ask

1. **"How do you measure if an agent is working well?"**
   → Six categories: success rate, efficiency, cost, safety, latency, quality. Track all six. Alert on degradation.

2. **"What's a good success rate for a production agent?"**
   → Depends on use case: internal tools > 85%, customer-facing > 95%. Also measure partial success for complex tasks.

3. **"How do you measure hallucination rate?"**
   → LLM-as-judge: separate model scores faithfulness and factual accuracy. Automated tools: Ragas faithfulness score. Ground truth comparison where available. Continuous evaluation, not just periodic.

4. **"How do you optimize cost without sacrificing quality?"**
   → Model routing (cheap model for easy tasks), semantic caching, prompt compression, output length limits. Always measure quality before and after cost optimization.

5. **"What metrics would you alert on?"**
   → Success rate drop > 5%, P99 latency > threshold, any safety violations, cost spike > 2x average, hallucination rate > 5%.

---

## Common Mistakes

⚠️ **Only tracking success/failure** — Binary success misses quality degradation. A "successful" response can still be wrong.

⚠️ **No cost tracking** — LLM costs are invisible until the bill arrives. Track cost per request from day one.

⚠️ **Measuring in dev only** — Production behavior differs from dev. Measure continuously in production.

⚠️ **No baselines** — Metrics without baselines are meaningless. Establish baselines before optimizing.

⚠️ **Vanity metrics** — "99% of requests got a response" means nothing if the responses are wrong. Measure quality, not just availability.

---

## TL;DR

- **Six metric categories:** Success, Efficiency, Cost, Safety, Latency, Quality
- **Success rate** = primary metric (> 90% for production)
- **Cost** = track per request, alert on spikes
- **Hallucination rate** = measure with LLM-as-judge or automated tools
- **Measure continuously in production** — not just during development
