# Observability

## What It Is

- **Observability** = the ability to understand what your agent is doing, why, and how well
- Three pillars: **Tracing** (what happened), **Metrics** (how well), **Logging** (details)
- Agent-specific additions: **behavioral evaluation** and **drift detection**
- Without observability, agents are black boxes — you can't debug, improve, or trust them

## Why It Matters (Interview Framing)

> "Observability is the difference between 'it works in my notebook' and 'it works in production.' Interviewers will ask how you debug a failing agent, measure quality, and detect degradation. This is your answer."

---

## Simple Mental Model

> Observability for agents is like a **flight data recorder (black box) for planes:**
> - Every decision the agent makes is recorded
> - Every tool call and result is logged
> - If something goes wrong, you can replay exactly what happened
> - You can measure performance trends over time

---

## The Observability Stack

```
┌──────────────────────────────────────────────────────┐
│              OBSERVABILITY STACK                       │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  TRACING (What happened)                     │    │
│  │  LangSmith, Arize Phoenix, OpenTelemetry     │    │
│  │                                              │    │
│  │  Agent Run ─▶ Step 1 ─▶ Step 2 ─▶ Result    │    │
│  │     │          │          │                   │    │
│  │   Thought   Tool call   Thought              │    │
│  │   Action    Result      Final answer          │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  METRICS (How well)                          │    │
│  │  Datadog, Prometheus, Grafana                │    │
│  │                                              │    │
│  │  Success rate, Latency, Cost, Error rate     │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  LOGGING (Details)                           │    │
│  │  Structured logs (JSON), ELK/CloudWatch      │    │
│  │                                              │    │
│  │  Every LLM call, tool call, error, decision  │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  BEHAVIORAL EVAL (Quality over time)         │    │
│  │  Ragas, TruLens, DeepEval                    │    │
│  │                                              │    │
│  │  Task quality, hallucination rate, relevance  │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  DRIFT DETECTION (Degradation)               │    │
│  │  Statistical monitoring, quality regression   │    │
│  │                                              │    │
│  │  Model drift, data drift, behavior drift     │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

---

## Pillar 1: Tracing

**What:** End-to-end trace of every agent run — every thought, action, and observation.

```
Trace: agent_run_abc123
│
├─ Span: planning (250ms)
│   └─ LLM call: gpt-4o (180ms, 450 tokens)
│
├─ Span: step_1_research (1200ms)
│   ├─ LLM call: gpt-4o (200ms, 300 tokens)
│   └─ Tool call: web_search (950ms)
│       └─ Result: 5 articles found
│
├─ Span: step_2_analysis (800ms)
│   ├─ LLM call: gpt-4o-mini (150ms, 200 tokens)
│   └─ Tool call: run_python (600ms)
│       └─ Result: chart_generated.png
│
├─ Span: step_3_synthesis (400ms)
│   └─ LLM call: gpt-4o (350ms, 800 tokens)
│
└─ Total: 2650ms, 1750 tokens, $0.045
```

**Tools:**

| Tool | Type | Strengths |
|---|---|---|
| **LangSmith** | Managed | Best for LangChain/LangGraph, built-in eval |
| **Arize Phoenix** | Open-source | Traces + evals, works with any framework |
| **OpenTelemetry** | Standard | Universal tracing, integrates with existing infra |
| **Datadog APM** | Managed | Full-stack tracing, correlate with infra metrics |
| **Braintrust** | Managed | Tracing + eval + prompt management |

---

## Pillar 2: Metrics

**Key metrics for agent systems:**

| Metric | What It Measures | Alert Threshold |
|---|---|---|
| **Task success rate** | % of agent runs that achieve the goal | < 90% |
| **Average latency** | Time from request to response | > 30s (depends on task) |
| **P99 latency** | Worst-case latency | > 120s |
| **Cost per request** | Total LLM + tool cost per run | > $X (your budget) |
| **Error rate** | % of runs that fail/error | > 5% |
| **Tool call failure rate** | % of tool calls that fail | > 10% |
| **Steps per task** | Average reasoning steps | Trending up (regression) |
| **Human escalation rate** | % of runs needing human | Trending up |
| **Hallucination rate** | % of outputs with hallucinated content | > 5% |
| **Token usage** | Avg tokens per run | Trending up (prompt bloat) |

**Dashboard layout:**

```
┌──────────────────────────────────────────────────┐
│  AGENT DASHBOARD                                  │
│                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │Success Rate│  │Avg Latency │  │ Cost/Run   │ │
│  │   94.2%    │  │   12.3s    │  │  $0.045    │ │
│  │   ▲ 1.2%   │  │   ▼ 2.1s   │  │  ▼ $0.01   │ │
│  └────────────┘  └────────────┘  └────────────┘ │
│                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ Error Rate │  │ HITL Rate  │  │ Halluc.    │ │
│  │   3.1%     │  │   8.5%     │  │   2.3%     │ │
│  └────────────┘  └────────────┘  └────────────┘ │
│                                                  │
│  [Success Rate Over Time - line chart]           │
│  [Cost Distribution - histogram]                 │
│  [Error Types - pie chart]                       │
└──────────────────────────────────────────────────┘
```

---

## Pillar 3: Logging

**Structured log format:**

```json
{
  "timestamp": "2025-03-15T10:23:45Z",
  "trace_id": "agent_run_abc123",
  "step": 2,
  "type": "tool_call",
  "tool": "web_search",
  "input": {"query": "competitor pricing analysis"},
  "output": {"results": 5, "status": "success"},
  "latency_ms": 950,
  "tokens_used": 0,
  "cost_usd": 0.002,
  "user_id": "user_456",
  "agent_id": "research_agent"
}
```

**Log everything:**
- Every LLM call (input, output, model, tokens, latency)
- Every tool call (name, args, result, latency, errors)
- Every agent decision (which tool, why, confidence)
- Every error (type, message, stack trace, context)
- Every guardrail trigger (what was blocked, why)

---

## Behavioral Evaluation

**Continuous quality evaluation — not just "did it run?" but "was the output good?"**

```
Agent Output → Evaluation Pipeline
                    │
                    ├── Relevance Score (0-1)
                    ├── Faithfulness Score (0-1)
                    ├── Hallucination Check (yes/no)
                    ├── Completeness Score (0-1)
                    └── Safety Check (pass/fail)
```

**Tools:**
- **Ragas:** RAG-specific evaluation (faithfulness, relevance, context)
- **TruLens:** General LLM app evaluation
- **DeepEval:** Unit testing for LLM outputs
- **Arize Phoenix:** Tracing + evaluation combined

---

## Drift Detection

**What:** Detecting when agent behavior or quality degrades over time.

| Drift Type | What Changes | Detection |
|---|---|---|
| **Model drift** | LLM provider updates model | Monitor quality metrics after model version changes |
| **Data drift** | Input distribution changes | Track input characteristics (length, topic, complexity) |
| **Behavior drift** | Agent starts taking different actions | Monitor action distributions, step counts |
| **Quality drift** | Output quality degrades | Continuous evaluation scores, user feedback |

```
Detection pipeline:
  Hourly eval scores → Rolling average → Compare to baseline
                                            │
                                ┌───────────┼───────────┐
                                │           │           │
                             Normal    Warning      Alert
                            (±1 std)  (±2 std)    (±3 std)
                                        │           │
                                    Investigate   Rollback
```

---

## Interview Questions They Will Ask

1. **"How do you debug a failing agent in production?"**
   → Pull the trace for the failed run. Walk through each step: what did the agent think? What tool did it call? What was the result? Where did it go wrong? Fix the root cause (prompt, tool, or logic).

2. **"What metrics would you track for an agent system?"**
   → Success rate, latency, cost per run, error rate, hallucination rate, tool failure rate, HITL escalation rate, token usage.

3. **"How do you detect quality degradation?"**
   → Continuous evaluation pipeline: score outputs on relevance, faithfulness, completeness. Track scores over time. Alert on statistical deviation from baseline.

4. **"What observability tools would you use?"**
   → LangSmith or Phoenix for tracing, Datadog/Prometheus for metrics, structured logging to ELK/CloudWatch, Ragas/TruLens for behavioral evaluation.

5. **"How do you handle LLM provider model updates?"**
   → Pin model versions in production. When provider releases new version: eval on test set → compare metrics → gradual rollout (canary) → full deploy if metrics improve.

---

## Common Mistakes

⚠️ **No tracing** — Without traces, you can't debug. Agent runs are multi-step — you need to see every step.

⚠️ **Only tracking success/failure** — Binary metrics miss quality degradation. An agent can "succeed" with a bad answer.

⚠️ **No baseline** — Without a baseline, you don't know if 85% success is good or bad. Establish baselines early.

⚠️ **Ignoring cost metrics** — Cost can spike without quality improving. Track cost efficiency (quality per dollar).

⚠️ **Manual evaluation only** — You can't manually review every agent run. Build automated evaluation into the pipeline.

---

## TL;DR

- **Three pillars:** Tracing (what happened), Metrics (how well), Logging (details)
- **Agent-specific additions:** Behavioral evaluation + drift detection
- **Key metrics:** Success rate, latency, cost, error rate, hallucination rate
- Use **LangSmith/Phoenix** for tracing, **Ragas/TruLens** for evaluation
- **Automate evaluation** — you can't manually review at scale
