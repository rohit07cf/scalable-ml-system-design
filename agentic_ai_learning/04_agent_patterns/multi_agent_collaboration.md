# Multi-Agent Collaboration

## What It Is

- **Multiple specialized agents** working together to accomplish a goal
- Each agent has a distinct role, tools, and expertise
- Agents communicate, delegate, debate, and verify each other's work
- Patterns: debate, delegation, voting, consensus, pipeline

## Why It Matters (Interview Framing)

> "Multi-agent collaboration is the hottest topic in AI engineering interviews right now. It tests your ability to think about distributed systems, communication protocols, and emergent behavior — but with LLMs as the compute units."

---

## Simple Mental Model

> A multi-agent system is like a **cross-functional team:**
> - Researcher gathers data
> - Analyst processes it
> - Writer creates the report
> - Reviewer quality-checks it
> - Each has their specialty, and they pass work between them

---

## Collaboration Patterns

### 1. Pipeline (Sequential)

```
Agent A ──▶ Agent B ──▶ Agent C ──▶ Result
(Research)  (Analyze)  (Write)
```

- Each agent processes and passes to the next
- Simple, predictable
- Failure in any stage blocks the pipeline

### 2. Debate (Adversarial)

```
┌──────────┐     argue      ┌──────────┐
│ Agent A   │◀──────────────▶│ Agent B   │
│ (Pro)     │               │ (Con)     │
└─────┬─────┘               └─────┬─────┘
      │                           │
      └─────────────┬─────────────┘
                    │
              ┌─────▼─────┐
              │   JUDGE   │
              │  (picks   │
              │  winner)  │
              └───────────┘
```

- Two agents argue opposing positions
- A judge agent evaluates and selects the best answer
- Excellent for reducing hallucinations and bias
- Expensive (3+ agents per query)

### 3. Delegation (Hierarchical)

```
              ┌──────────┐
              │SUPERVISOR│
              └────┬─────┘
           ┌───────┼────────┐
           ▼       ▼        ▼
      ┌────────┐┌────────┐┌────────┐
      │Worker A││Worker B││Worker C│
      └────────┘└────────┘└────────┘
```

- Supervisor assigns tasks to specialist workers
- Workers report results back
- Supervisor synthesizes and decides next action
- Most common production pattern

### 4. Voting / Consensus

```
      Query
     /  |  \
    ▼   ▼   ▼
  [A]  [B]  [C]   ← 3 agents generate answers independently
    \   |   /
     ▼  ▼  ▼
   [Majority Vote]  ← Pick the most common answer
```

- Multiple agents independently answer the same question
- Majority vote or confidence-weighted selection
- Reduces hallucination at the cost of 3x compute
- Good for high-stakes decisions

### 5. Peer Review

```
Agent A → Draft → Agent B → Review → Agent A → Revise → Final
```

- One agent creates, another reviews
- Iterative improvement through feedback cycles
- Similar to code review in software engineering

---

## Communication Patterns

| Pattern | How Agents Communicate | Pros | Cons |
|---|---|---|---|
| **Shared memory** | Read/write to shared state (Redis, DB) | Simple, fast | Race conditions |
| **Message passing** | Send messages to each other | Decoupled, scalable | More complex |
| **Blackboard** | Shared workspace all agents read/write | Flexible | Coordination overhead |
| **Event-driven** | Agents react to events/triggers | Loosely coupled | Harder to debug |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           MULTI-AGENT SYSTEM                     │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │           ORCHESTRATOR                     │  │
│  │  (routes tasks, manages state, decides     │  │
│  │   which agent to invoke next)              │  │
│  └──────────────────┬────────────────────────┘  │
│         ┌───────────┼───────────┐               │
│         ▼           ▼           ▼               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Research  │ │Analysis  │ │Writing   │       │
│  │Agent     │ │Agent     │ │Agent     │       │
│  │          │ │          │ │          │       │
│  │Tools:    │ │Tools:    │ │Tools:    │       │
│  │- search  │ │- python  │ │- llm     │       │
│  │- scrape  │ │- sql     │ │- format  │       │
│  └──────────┘ └──────────┘ └──────────┘       │
│         │           │           │               │
│  ┌──────┴───────────┴───────────┴──────────┐   │
│  │          SHARED STATE (Redis)            │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Practical Example: Due Diligence Agent Team

```
Goal: "Perform due diligence on TargetCo for acquisition"

ORCHESTRATOR assigns:

Research Agent:
  - Search for TargetCo financials
  - Gather market position data
  - Find news and press releases
  → Output: Research Report

Financial Agent:
  - Analyze revenue trends
  - Calculate valuation multiples
  - Compare to industry benchmarks
  → Output: Financial Analysis

Legal Agent:
  - Check regulatory filings
  - Identify pending litigation
  - Review compliance history
  → Output: Legal Risk Assessment

Synthesis Agent:
  - Combine all reports
  - Identify key risks and opportunities
  - Generate executive recommendation
  → Output: Due Diligence Report

ORCHESTRATOR: Compile → Review → Deliver
```

---

## Interview Questions They Will Ask

1. **"How do agents communicate in a multi-agent system?"**
   → Four patterns: shared memory, message passing, blackboard, event-driven. Production systems typically use shared state (Redis) + message passing for coordination.

2. **"How do you prevent agents from conflicting with each other?"**
   → Clear role definitions (non-overlapping responsibilities), shared state with locks/versioning, supervisor to resolve conflicts, defined communication protocols.

3. **"When would you use multi-agent debate?"**
   → High-stakes decisions where hallucination is dangerous. Two agents argue, a judge decides. More expensive but significantly reduces errors.

4. **"How do you debug a multi-agent system?"**
   → Trace every inter-agent message. Log each agent's reasoning. Replay conversations. Use tools like LangSmith to visualize the full execution graph.

5. **"What's the overhead of multi-agent vs single agent?"**
   → 2-5x more LLM calls, more complex orchestration, harder to debug. Worth it when: task requires specialization, quality matters more than cost, single agent can't handle complexity.

---

## Common Mistakes

⚠️ **Too many agents** — Start with 2-3. Every additional agent adds communication overhead and failure modes.

⚠️ **Overlapping roles** — If two agents can do the same thing, they'll conflict. Define clear, non-overlapping responsibilities.

⚠️ **No orchestrator** — Without a coordinator, agents talk past each other or do redundant work.

⚠️ **Synchronous everything** — Independent agents should run in parallel. Only synchronize when one agent needs another's output.

⚠️ **Ignoring cost** — A 4-agent system with 10 steps each = 40 LLM calls. Budget accordingly.

---

## TL;DR

- Multi-agent = **specialized agents collaborating** on a shared goal
- Key patterns: **Pipeline, Debate, Delegation, Voting, Peer Review**
- Communication via **shared state, messages, or events**
- Always have an **orchestrator** to coordinate agents
- Start with **2-3 agents** — add more only when justified by task complexity
