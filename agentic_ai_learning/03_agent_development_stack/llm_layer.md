# LLM Layer

## What It Is

- The **foundation model** that powers the agent's reasoning, planning, and text generation
- Choosing the right LLM = balancing cost, latency, quality, and context window
- Not all tasks need the most powerful model — multi-model strategies are common
- The LLM layer is the "brain" of the agent stack

## Why It Matters (Interview Framing)

> "Model selection is an architecture decision, not a preference. Interviewers want to see that you can justify GPT-4o vs Claude vs Gemini based on task requirements, cost, latency, and context window — not hype."

---

## Model Landscape (2025)

| Model | Provider | Context Window | Strengths | Best For |
|---|---|---|---|---|
| **GPT-4o** | OpenAI | 128K | Strong reasoning, tool use, multimodal | General-purpose agents |
| **GPT-4o-mini** | OpenAI | 128K | Fast, cheap, good enough for many tasks | High-volume, cost-sensitive |
| **Claude 3.5 Sonnet** | Anthropic | 200K | Excellent coding, long context, safety | Code agents, document analysis |
| **Claude 3 Opus** | Anthropic | 200K | Strongest reasoning | Complex planning, high-stakes |
| **Gemini 1.5 Pro** | Google | 1M+ | Massive context window, multimodal | Huge document processing |
| **Gemini 2.0 Flash** | Google | 1M | Fast, good quality | Cost-effective, high-throughput |
| **Mistral Large** | Mistral | 128K | Open-weight compatible, strong EU compliance | EU-regulated, self-hosted |
| **Llama 3.x** | Meta | 128K | Open-source, self-hostable | Privacy-sensitive, on-prem |

---

## Key Dimensions for Model Selection

### Context Window

```
Small context (4-8K):    [████░░░░░░░░░░░░░░░░] Limited — single-task agents
Medium context (32-128K): [████████████░░░░░░░░] Good — most agent workflows
Large context (200K-1M):  [████████████████████] Excellent — document analysis, RAG
```

- **Why it matters:** Agent context = system prompt + tools + memory + conversation + retrieved docs
- A 10-step ReAct loop can easily consume 20-50K tokens
- Multi-agent systems multiply context needs

💡 **Rule of thumb:** Estimate your worst-case context usage. Pick a model with 2x headroom.

### Token Pricing (Cost Architecture)

```
Cost per agent run = Σ (input_tokens × input_price + output_tokens × output_price)
                     for each LLM call in the reasoning loop
```

| Strategy | Description |
|---|---|
| **Single model** | One model for everything — simple but expensive |
| **Router model** | Cheap model classifies task, expensive model handles complex ones |
| **Cascade** | Try cheap model first, escalate to expensive if quality is low |
| **Multi-model** | Different models for different tasks (plan with GPT-4o, execute with mini) |

💡 **Interview insight:** "We use a router pattern — GPT-4o-mini handles 80% of requests, GPT-4o handles the remaining 20% requiring complex reasoning. This cuts cost by 60%."

### Latency

| Model Tier | Typical TTFT | Tokens/sec | Use Case |
|---|---|---|---|
| **Frontier** (GPT-4o, Claude 3 Opus) | 500-2000ms | 30-60 | Quality-critical |
| **Fast** (GPT-4o-mini, Gemini Flash) | 100-500ms | 60-120 | Latency-sensitive |
| **Self-hosted** (Llama, Mistral) | Variable | Depends on infra | Privacy-critical |

---

## Architecture Diagram: LLM Layer in the Stack

```
┌─────────────────────────────────────────────┐
│              AGENT ORCHESTRATOR              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │          LLM LAYER                  │    │
│  │                                     │    │
│  │  ┌──────────┐   ┌──────────────┐   │    │
│  │  │  Router   │──▶│ Model Pool    │   │    │
│  │  │  (classify│   │              │   │    │
│  │  │   task)   │   │ ┌──────────┐ │   │    │
│  │  └──────────┘   │ │ GPT-4o   │ │   │    │
│  │                  │ │ Claude   │ │   │    │
│  │                  │ │ Gemini   │ │   │    │
│  │                  │ │ Llama    │ │   │    │
│  │                  │ └──────────┘ │   │    │
│  │                  └──────────────┘   │    │
│  │                                     │    │
│  │  ┌──────────┐   ┌──────────────┐   │    │
│  │  │  Cache    │   │ Rate Limiter │   │    │
│  │  │(semantic) │   │ + Fallback   │   │    │
│  │  └──────────┘   └──────────────┘   │    │
│  └─────────────────────────────────────┘    │
│                                             │
├─────────────────────────────────────────────┤
│     TOOLS  │  MEMORY  │  EXECUTION          │
└─────────────────────────────────────────────┘
```

---

## Multi-Model Strategy Example

```python
class ModelRouter:
    def select_model(self, task):
        if task.requires_complex_reasoning:
            return "gpt-4o"          # Best reasoning
        elif task.requires_long_context:
            return "gemini-1.5-pro"  # 1M context
        elif task.requires_code:
            return "claude-3.5-sonnet"  # Best at code
        elif task.is_simple:
            return "gpt-4o-mini"     # Cheap + fast
        else:
            return "gpt-4o"          # Default
```

---

## Interview Questions They Will Ask

1. **"How do you choose which LLM to use for an agent?"**
   → Evaluate: task complexity (reasoning quality), context needs (window size), latency requirements, cost budget, compliance needs (data residency). Use a router pattern for mixed workloads.

2. **"How do you reduce LLM costs in an agent system?"**
   → Model routing (cheap model for easy tasks), semantic caching, prompt compression, shorter system prompts, output length limits, batch processing for non-real-time tasks.

3. **"What happens when the LLM API goes down?"**
   → Fallback chain: primary → secondary → cached response → graceful degradation. Circuit breaker pattern. Never let a single provider outage take down the system.

4. **"How do context windows affect agent design?"**
   → Larger windows allow more memory, more tools, more history in context. But: more tokens = more cost + latency. Design for efficient context use — don't waste tokens.

5. **"Self-hosted vs API-based LLMs?"**
   → API = fastest to ship, scales automatically, best models. Self-hosted = data privacy, no vendor lock-in, higher infra cost. Use API for speed, self-host for sensitive data.

---

## Common Mistakes

⚠️ **Always using the most expensive model** — GPT-4o-mini handles 80% of tasks fine. Don't burn money on frontier models for classification tasks.

⚠️ **No fallback strategy** — API outages happen. Have a secondary model configured and tested.

⚠️ **Ignoring context window efficiency** — Stuffing 100K tokens when 10K would suffice. Every token costs money and adds latency.

⚠️ **Not benchmarking for YOUR task** — Model leaderboards test general ability. Your agent's tasks may favor a different model. Always benchmark on representative samples.

⚠️ **Vendor lock-in** — Abstract the LLM call behind an interface. Switching from OpenAI to Anthropic should be a config change, not a rewrite.

---

## TL;DR

- **Model selection** = balance of quality, cost, latency, and context window
- Use **multi-model strategies** (router, cascade) to optimize cost
- **Context window** is a critical constraint — estimate worst-case usage
- Always have a **fallback model** for API outages
- **Abstract the LLM layer** — avoid vendor lock-in
