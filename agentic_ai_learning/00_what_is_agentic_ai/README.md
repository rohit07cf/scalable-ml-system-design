# What Is Agentic AI?

## What It Is

- **Agentic AI** = AI systems that can **plan, reason, act, and self-correct** to achieve goals autonomously
- Unlike GenAI (which produces outputs), Agentic AI drives **outcomes** through multi-step workflows
- An agent = LLM + Tools + Memory + Reasoning Loop
- The key shift: from "answer my question" to "accomplish my objective"

## Why It Matters (Interview Framing)

> "The industry is moving from AI-as-a-tool to AI-as-a-worker. Every major platform — Microsoft, Google, OpenAI, Anthropic — is investing in agent architectures. Understanding agentic design is now a core interview expectation for AI engineers."

---

## GenAI vs Agentic AI

| Dimension | GenAI (Traditional LLM) | Agentic AI |
|---|---|---|
| **Interaction** | Single turn: prompt → response | Multi-turn: goal → plan → actions → result |
| **Output** | Text, code, images | Completed tasks, decisions, workflows |
| **Memory** | Stateless (per request) | Stateful (short + long-term memory) |
| **Tools** | None (text only) | APIs, code exec, DB, browser, files |
| **Self-correction** | None | Evaluates own output, retries, adapts |
| **Autonomy** | Zero — user drives everything | Configurable — from co-pilot to autopilot |
| **Architecture** | LLM call | LLM + Orchestrator + Tools + Memory |

💡 **Interview Phrase:** *"GenAI produces outputs. Agentic AI delivers outcomes."*

---

## The Four Pillars of Agentic AI

```
              ┌──────────────┐
              │     GOAL     │
              └──────┬───────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼───┐ ┌─────▼────┐ ┌───▼────────┐
    │PLANNING│ │REASONING │ │COLLABORATION│
    │        │ │ + ACTING  │ │             │
    └────┬───┘ └─────┬────┘ └───┬────────┘
         │           │           │
         └───────────┼───────────┘
                     │
              ┌──────▼───────┐
              │SELF-EVALUATION│
              └──────────────┘
```

| Pillar | What It Does |
|---|---|
| **Planning** | Decomposes goal into subtasks, orders them, handles dependencies |
| **Reasoning + Acting** | Thinks step-by-step, calls tools, processes results (ReAct loop) |
| **Collaboration** | Multiple agents work together — debate, delegate, verify |
| **Self-Evaluation** | Checks own output quality, retries on failure, learns from mistakes |

---

## The Reasoning + Acting Loop (Core Engine)

```
     ┌──────────┐
     │  OBSERVE  │ ← Perceive environment / input
     └────┬─────┘
          │
     ┌────▼─────┐
     │  THINK   │ ← Reason about what to do (CoT / ReAct)
     └────┬─────┘
          │
     ┌────▼─────┐
     │   ACT    │ ← Call tool / execute action
     └────┬─────┘
          │
     ┌────▼─────┐
     │ EVALUATE │ ← Did it work? Is the goal met?
     └────┬─────┘
          │
          ├── YES → Return result
          └── NO  → Loop back to OBSERVE
```

💡 **This loop is the heart of every agent pattern.** ReAct, Plan-and-Execute, OODA — they're all variations of this.

---

## Simple Mental Model

> Think of Agentic AI like a **junior developer with superpowers:**
> - They receive a task (goal)
> - They break it into steps (planning)
> - They write code, run tests, read docs (tool use)
> - They check if it works (self-evaluation)
> - They ask for help or escalate if stuck (human-in-the-loop)
> - They remember past context (memory)

---

## Practical Example

**Goal:** "Find the top 3 competitors for Acme Corp and create a comparison report"

```
Agent receives goal
  │
  ├─ PLAN: Decompose into subtasks
  │   ├─ 1. Search web for Acme Corp competitors
  │   ├─ 2. For each competitor, gather revenue + product data
  │   ├─ 3. Compile comparison table
  │   └─ 4. Generate executive summary
  │
  ├─ ACT: Execute step 1
  │   └─ Tool: web_search("Acme Corp competitors 2025")
  │   └─ Result: [CompA, CompB, CompC, CompD, CompE]
  │
  ├─ EVALUATE: Too many results → refine to top 3 by market cap
  │
  ├─ ACT: Execute step 2 (for each of top 3)
  │   └─ Tool: web_search, financial_api
  │
  ├─ ACT: Execute step 3
  │   └─ Tool: code_interpreter (generate table)
  │
  ├─ EVALUATE: Check table completeness
  │
  └─ ACT: Execute step 4 → Return report
```

---

## Interview Questions They Will Ask

1. **"What makes an AI system 'agentic' vs just a chatbot?"**
   → Autonomy, tool use, memory, reasoning loops, self-correction

2. **"Explain the difference between GenAI and Agentic AI."**
   → Use the table above. Emphasize output vs outcome.

3. **"What are the risks of giving AI more autonomy?"**
   → Hallucination cascades, uncontrolled tool calls, cost explosion, safety violations

4. **"When would you NOT use an agentic approach?"**
   → Simple Q&A, low-latency requirements, deterministic workflows, cost-sensitive scenarios

5. **"How does an agent decide what to do next?"**
   → Reasoning loop: observe → think → act → evaluate → repeat

---

## Common Mistakes

⚠️ **Calling any LLM app "agentic"** — If there's no reasoning loop or tool use, it's just a prompt chain

⚠️ **Thinking agents are always better** — For simple tasks, a single LLM call is faster, cheaper, and more reliable

⚠️ **Ignoring cost** — Each reasoning step = more tokens = more money. A 10-step agent costs 10x a single call

⚠️ **No human-in-the-loop** — Production agents need escape hatches and approval gates

⚠️ **Conflating "agent" with "autonomous"** — Agents exist on a spectrum from co-pilot to fully autonomous

---

## TL;DR

- **Agentic AI** = LLM + Tools + Memory + Reasoning Loop → achieves goals autonomously
- Core loop: **Observe → Think → Act → Evaluate → Repeat**
- GenAI = outputs, Agentic AI = **outcomes**
- Four pillars: **Planning, Reasoning+Acting, Collaboration, Self-Evaluation**
- Always consider: **cost, latency, safety, and when NOT to use agents**

---

*Next: [01_core_concepts/reasoning_loops.md](../01_core_concepts/reasoning_loops.md) →*
