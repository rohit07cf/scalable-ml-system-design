# Cost & Latency Analysis

## What It Is

- **Cost analysis** = understanding and optimizing how much each agent run costs
- **Latency analysis** = understanding and optimizing how long each agent run takes
- Cost and latency are the two biggest practical barriers to production agent deployment
- They're often in tension: reducing cost can increase latency, and vice versa

## Why It Matters (Interview Framing)

> "Interviewers love asking 'What would this cost at scale?' and 'How fast is it?' because it tests if you've actually built production systems. Being able to estimate $0.05/request × 100K requests/day = $5K/day shows real-world thinking."

---

## Cost Breakdown

### Where the Money Goes

```
Total Cost per Agent Run:
┌─────────────────────────────────────────────┐
│                                             │
│  LLM Token Costs        ████████████  65%   │
│  Tool/API Costs          ████          15%   │
│  Infrastructure           ███          10%   │
│  Vector DB               ██            5%   │
│  Embedding                █             3%   │
│  Other                    █             2%   │
│                                             │
└─────────────────────────────────────────────┘
```

### LLM Cost Formula

```
LLM Cost = Σ (input_tokens × input_price) + (output_tokens × output_price)
           for each LLM call in the agent run
```

**Current pricing (approximate, per 1M tokens):**

| Model | Input | Output | Notes |
|---|---|---|---|
| **GPT-4o** | $2.50 | $10.00 | Best general quality |
| **GPT-4o-mini** | $0.15 | $0.60 | Great cost/quality ratio |
| **Claude 3.5 Sonnet** | $3.00 | $15.00 | Best for code |
| **Claude 3 Haiku** | $0.25 | $1.25 | Fast and cheap |
| **Gemini 1.5 Pro** | $1.25 | $5.00 | Huge context window |
| **Gemini 2.0 Flash** | $0.10 | $0.40 | Cheapest for quality |

### Cost Per Agent Run Example

```
Agent: Customer support (5-step ReAct)

Step 1: Classify intent
  Input: 2,000 tokens (system + user message)
  Output: 50 tokens
  Cost: $0.0005 (GPT-4o-mini)

Step 2: Search knowledge base
  Input: 3,000 tokens (system + history + query)
  Output: 100 tokens
  Cost: $0.0005
  + Embedding: $0.0001
  + Vector DB query: $0.0001

Step 3: Read relevant documents
  Input: 5,000 tokens (system + history + retrieved docs)
  Output: 200 tokens
  Cost: $0.0009

Step 4: Generate response
  Input: 6,000 tokens (full context)
  Output: 500 tokens
  Cost: $0.0012

Step 5: Guardrail check
  Input: 1,000 tokens
  Output: 50 tokens
  Cost: $0.0002

─────────────────────────────
Total: ~$0.0035 per request
At 10K requests/day: $35/day = ~$1,050/month
At 100K requests/day: $350/day = ~$10,500/month
```

---

## Cost Optimization Strategies

| Strategy | Impact | Effort | How |
|---|---|---|---|
| **Model routing** | 40-60% savings | Medium | Cheap model for easy tasks, expensive for hard |
| **Semantic caching** | 20-40% savings | Medium | Cache similar queries → same answer |
| **Prompt compression** | 10-20% savings | Low | Shorter system prompts, remove redundant context |
| **Output limits** | 5-15% savings | Low | Max output tokens per step |
| **Batch processing** | 30-50% savings | Medium | Batch non-real-time requests (often cheaper rates) |
| **Self-hosted models** | 50-80% savings | High | Run open-source models on your infra |

```
Cost optimization decision tree:

Is the task simple?
  └─ YES → Use cheapest model (GPT-4o-mini, Gemini Flash)
  └─ NO →
      Is the same query asked often?
        └─ YES → Add semantic caching
        └─ NO →
            Is real-time needed?
              └─ NO → Use batch API (50% cheaper)
              └─ YES → Use model routing (cheap default, expensive escalation)
```

---

## Latency Breakdown

### Where Time Goes

```
Agent Run Latency Breakdown:
┌─────────────────────────────────────────────┐
│                                             │
│  LLM Inference (TTFT)    ████████████  55%  │
│  Tool Execution          ██████        25%  │
│  Network overhead         ██            8%  │
│  Embedding/Vector search  ██            7%  │
│  Orchestration overhead    █            5%  │
│                                             │
└─────────────────────────────────────────────┘
```

### Latency Per Component

| Component | Typical Latency | Notes |
|---|---|---|
| **LLM call (frontier)** | 500-2000ms | Varies by input/output size |
| **LLM call (fast)** | 100-500ms | GPT-4o-mini, Gemini Flash |
| **Tool call (API)** | 200-2000ms | Depends on external service |
| **Tool call (DB)** | 10-100ms | Local/managed DB |
| **Vector search** | 20-100ms | Depends on index size |
| **Embedding** | 50-200ms | Per query |
| **Orchestration** | 10-50ms | Framework overhead per step |

### Total Latency Formula

```
Total Latency = Σ (llm_latency + tool_latency + overhead) × num_steps

Example (5-step agent):
  5 × (300ms LLM + 500ms tool + 20ms overhead)
  = 5 × 820ms
  = 4.1 seconds total
```

---

## Latency Optimization Strategies

| Strategy | Impact | How |
|---|---|---|
| **Streaming** | Perceived latency → near-zero | Stream tokens as generated |
| **Parallel tool calls** | 30-50% reduction | Run independent tools concurrently |
| **Faster model** | 40-60% reduction | GPT-4o-mini instead of GPT-4o |
| **Prompt reduction** | 10-20% reduction | Fewer input tokens = faster inference |
| **Caching** | 90%+ for cache hits | Skip LLM entirely for cached queries |
| **Speculative execution** | 20-30% reduction | Start next step before current finishes |
| **Edge deployment** | 30-50% reduction | Reduce network hops |

```
Latency optimization priority:
  1. Enable streaming (immediate perceived improvement)
  2. Add caching (free for repeated queries)
  3. Use faster model for simple steps
  4. Parallelize independent tool calls
  5. Optimize prompts (reduce input tokens)
```

---

## Cost vs Latency Trade-off

```
                High Quality
                    │
         Expensive  │  Fast + Expensive
         + Slow     │  (frontier model,
         (multiple  │   parallel, cached)
         reflections│
                    │
  ──────────────────┼──────────────────
                    │
         Cheap      │  Cheap + Fast
         + Slow     │  (small model,
         (queued,   │   cached,
         batched)   │   minimal steps)
                    │
                Low Quality
```

| If you need... | Optimize for... | Accept... |
|---|---|---|
| Real-time customer support | Latency | Higher cost (faster models) |
| Batch report generation | Cost | Higher latency (queue + cheap models) |
| High-stakes financial analysis | Quality | Both cost and latency |
| Internal dev tool | Balance | Moderate cost and latency |

---

## Practical Example: Cost Projection

```python
def estimate_monthly_cost(
    requests_per_day,
    avg_steps_per_request=5,
    avg_tokens_per_step=3000,
    model="gpt-4o-mini"
):
    pricing = {
        "gpt-4o": {"input": 2.50, "output": 10.00},    # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3.5-sonnet": {"input": 3.00, "output": 15.00}
    }

    p = pricing[model]
    input_tokens = avg_tokens_per_step * avg_steps_per_request
    output_tokens = input_tokens * 0.2  # ~20% of input

    cost_per_request = (
        (input_tokens / 1_000_000) * p["input"] +
        (output_tokens / 1_000_000) * p["output"]
    )

    daily = cost_per_request * requests_per_day
    monthly = daily * 30

    return {
        "cost_per_request": f"${cost_per_request:.4f}",
        "daily_cost": f"${daily:.2f}",
        "monthly_cost": f"${monthly:.2f}"
    }

# Example outputs:
# GPT-4o-mini, 10K requests/day:
#   Per request: $0.0024, Daily: $24, Monthly: $720

# GPT-4o, 10K requests/day:
#   Per request: $0.0475, Daily: $475, Monthly: $14,250
```

---

## Continuous Evaluation Patterns

### Regression Testing

```
Before deploy:
  Run eval suite → Score ≥ baseline → Deploy ✅
  Run eval suite → Score < baseline → Block deploy ❌
```

### Canary Deployments

```
100% traffic → Old version
    │
Deploy canary (5% traffic → new version)
    │
Compare metrics:
  Success rate:   Old 94.2% vs New 95.1%  ✅
  Cost:           Old $0.045 vs New $0.038 ✅
  Latency:        Old 8.2s vs New 7.8s    ✅
  Hallucination:  Old 2.1% vs New 1.8%    ✅
    │
All better → Promote to 100% ✅
Any worse  → Rollback ❌
```

### Drift Detection

```
Sliding window (7 days):
  If metric_current < (metric_baseline - 2*std):
    ALERT: Quality regression detected
    Action: Investigate root cause
            → Model update? Data change? Prompt drift?
```

---

## Interview Questions They Will Ask

1. **"How much would this agent system cost at scale?"**
   → Calculate: tokens per request × price per token × requests per day. Example: 5-step agent using GPT-4o-mini at 10K requests/day ≈ $720/month. Add 15-20% for tools, infra, vector DB.

2. **"How do you reduce agent costs?"**
   → Model routing (biggest impact), semantic caching, prompt compression, batch processing. Always measure quality before and after — cheapest isn't best if quality drops.

3. **"What's the latency budget for an agent system?"**
   → Depends on use case. Real-time chat: < 10s. Async report: < 5 min. Streaming helps perceived latency. Most production agents: 5-30s end-to-end.

4. **"How do you do canary deployments for agents?"**
   → Route 5% of traffic to new version. Compare key metrics (success, cost, latency, quality) against old version. Promote if all metrics are equal or better. Rollback if any metric degrades.

5. **"How do you prevent cost explosion?"**
   → Budget limits per request ($X max), iteration limits (N max steps), token limits, rate limiting per user, alert on cost spikes, circuit breakers on expensive APIs.

---

## Common Mistakes

⚠️ **Not estimating cost before building** — Run the numbers first. A system that costs $50K/month in LLM calls may not be viable.

⚠️ **Optimizing cost at the expense of quality** — Switching to the cheapest model saves money but may tank quality. Always measure both.

⚠️ **Ignoring latency for async systems** — Even async systems need latency budgets. A 10-minute agent run may be acceptable; a 2-hour run probably isn't.

⚠️ **No cost alerts** — A single bad prompt or loop can generate thousands of API calls. Set alerts for daily cost thresholds.

⚠️ **Not accounting for growth** — 1K requests/day today might be 100K in 6 months. Model your cost curve and plan optimization early.

---

## TL;DR

- **LLM tokens = 65% of cost.** Model routing and caching have the biggest cost impact.
- **LLM inference = 55% of latency.** Streaming and faster models help most.
- **Always calculate:** tokens × price × requests × 30 = monthly cost
- Use **canary deployments** and **regression testing** for safe updates
- **Cost and quality are linked** — never optimize one without measuring the other
