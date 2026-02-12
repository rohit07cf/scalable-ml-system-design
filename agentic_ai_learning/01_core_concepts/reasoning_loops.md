# Reasoning Loops

## What It Is

- The **iterative thought process** an agent uses to decide its next action
- Each loop cycle: perceive → reason → act → observe result → reason again
- Different loop types optimize for different trade-offs (speed vs thoroughness)
- This is what separates an "agent" from a "prompt chain"

## Why It Matters (Interview Framing)

> "The reasoning loop is the **control flow** of an agent. Choosing the right loop pattern determines whether your agent is fast-but-shallow or thorough-but-expensive. Interviewers test if you can articulate these trade-offs."

---

## The Five Reasoning Loop Patterns

### 1. ReAct (Reasoning + Acting)

```
Thought: I need to find the user's order status
Action: call_api(order_service, GET /orders/123)
Observation: {status: "shipped", eta: "2025-03-15"}
Thought: I have the info, I can respond now
Action: respond("Your order shipped, arriving March 15")
```

- **How it works:** Interleave reasoning (Thought) with actions (tool calls)
- **Strength:** Grounded — every thought leads to a verifiable action
- **Weakness:** Sequential; can't explore multiple paths
- **When to use:** Most general-purpose agent tasks

💡 **This is the default pattern. If in doubt, use ReAct.**

---

### 2. Chain-of-Thought (CoT)

```
Question: What's 23 × 47?
Thought: 23 × 47 = 23 × 40 + 23 × 7 = 920 + 161 = 1081
Answer: 1081
```

- **How it works:** LLM "shows its work" before answering
- **Strength:** Improves accuracy on reasoning-heavy tasks
- **Weakness:** No external actions — purely internal reasoning
- **When to use:** Math, logic, multi-step reasoning without tool needs

⚠️ CoT alone doesn't make an agent. It's a **reasoning technique**, not an agent pattern.

---

### 3. Tree-of-Thought (ToT)

```
            ┌─ Path A: Use SQL query    → Score: 0.7
  Problem ──┤
            ├─ Path B: Use API endpoint → Score: 0.9  ← Selected
            │
            └─ Path C: Use cached data  → Score: 0.4
```

- **How it works:** Explore multiple reasoning paths, evaluate each, pick the best
- **Strength:** Better for problems with multiple valid approaches
- **Weakness:** Expensive — requires multiple LLM calls per step
- **When to use:** Complex planning, code generation, creative problem solving

---

### 4. OODA Loop (Observe-Orient-Decide-Act)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────┐
│ OBSERVE  │───▶│  ORIENT  │───▶│  DECIDE  │───▶│ ACT  │
│ (data in)│    │(context) │    │ (choose) │    │(exec)│
└──────────┘    └──────────┘    └──────────┘    └──────┘
     ▲                                              │
     └──────────────────────────────────────────────┘
```

- **How it works:** Military-inspired loop emphasizing **context awareness** (Orient phase)
- **Strength:** Excellent for dynamic, changing environments
- **Weakness:** Adds overhead for simple tasks
- **When to use:** Real-time monitoring agents, trading agents, security agents

---

### 5. Self-Correction Loops

```
Generate answer
    │
    ▼
Critique own answer  ← "Is this correct? Complete? Safe?"
    │
    ├── PASS → Return answer
    └── FAIL → Regenerate with critique as feedback
                    │
                    ▼
               Re-critique → (max 3 iterations)
```

- **How it works:** Agent generates, then reviews its own output
- **Strength:** Catches hallucinations and incomplete answers
- **Weakness:** Can loop forever without a max iteration limit
- **When to use:** High-stakes outputs (code, financial analysis, medical)

⚠️ **Always set a max iteration count.** Unbounded self-correction = infinite cost.

---

## Comparison Table

| Pattern | # LLM Calls | Tool Use | Best For | Cost |
|---|---|---|---|---|
| **ReAct** | Medium (sequential) | Yes | General agent tasks | Medium |
| **CoT** | 1 | No | Reasoning-only tasks | Low |
| **ToT** | High (branching) | Optional | Complex planning | High |
| **OODA** | Medium | Yes | Dynamic environments | Medium |
| **Self-Correction** | 2-4x base | Optional | High-stakes output | Medium-High |

---

## Architecture Diagram: How Loops Fit in an Agent

```
┌─────────────────────────────────────┐
│              AGENT                   │
│                                     │
│  ┌─────────────────────────────┐    │
│  │     REASONING LOOP          │    │
│  │  ┌────┐ ┌────┐ ┌────────┐  │    │
│  │  │Think│→│Act │→│Evaluate│──┤    │
│  │  └────┘ └────┘ └────────┘  │    │
│  │     ▲                  │    │    │
│  │     └──────────────────┘    │    │
│  └─────────────────────────────┘    │
│         │          │                │
│    ┌────▼───┐ ┌────▼───┐           │
│    │ MEMORY │ │ TOOLS  │           │
│    └────────┘ └────────┘           │
└─────────────────────────────────────┘
```

---

## Practical Example: Customer Support Agent

```python
# ReAct loop pseudocode
while not goal_achieved and iterations < MAX_ITER:
    thought = llm.reason(context + memory + last_observation)

    if thought.is_final_answer:
        return thought.answer

    action = thought.next_action          # e.g., "search_kb"
    observation = tools.execute(action)   # e.g., KB article content

    memory.add(thought, action, observation)
    iterations += 1
```

---

## Interview Questions They Will Ask

1. **"Explain the ReAct pattern."**
   → Interleaved reasoning and acting. Thought → Action → Observation → repeat.

2. **"When would you use Tree-of-Thought over Chain-of-Thought?"**
   → When multiple valid solution paths exist and you need to evaluate trade-offs.

3. **"How do you prevent infinite loops in self-correction?"**
   → Max iteration limits, diminishing improvement detection, timeout budgets.

4. **"What's the cost implication of different reasoning loops?"**
   → CoT = 1 call. ReAct = N calls (N = steps). ToT = branching factor × depth calls.

5. **"How do you choose which reasoning loop to use?"**
   → Simple reasoning → CoT. Tool-using tasks → ReAct. Complex planning → ToT. Dynamic env → OODA.

---

## Common Mistakes

⚠️ **Using ToT for simple tasks** — Massive overkill. Most tasks work fine with ReAct.

⚠️ **No iteration limits** — Every loop MUST have a max iteration count and token budget.

⚠️ **Confusing CoT with ReAct** — CoT has no actions/tools. ReAct interleaves thinking WITH doing.

⚠️ **Not logging loop iterations** — You need observability into each step for debugging.

⚠️ **Ignoring cost** — A 15-step ReAct loop with GPT-4o ≈ $0.50-2.00 per request.

---

## TL;DR

- **ReAct** = default agent loop (Thought → Action → Observation)
- **CoT** = reasoning-only, no tools (good for math/logic)
- **ToT** = explore multiple paths, pick best (expensive but thorough)
- **OODA** = context-aware loop for dynamic environments
- **Always set max iterations and token budgets** to prevent runaway costs
