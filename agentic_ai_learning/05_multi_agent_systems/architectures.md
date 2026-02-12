# Multi-Agent System Architectures

## What It Is

- **Multi-Agent Systems (MAS)** = multiple AI agents working together to accomplish goals beyond any single agent's capability
- Architecture defines how agents are organized, how they communicate, and who makes decisions
- Two primary dimensions: **organizational structure** (hierarchy vs flat) and **interaction mode** (collaborative vs competitive)
- MAS is the path to enterprise-scale agentic AI

## Why It Matters (Interview Framing)

> "Multi-agent architecture is the system design question for AI engineers. Interviewers will ask you to design a system with multiple specialized agents, and they'll probe: who orchestrates? How do agents communicate? How do you handle failures? This is distributed systems thinking applied to AI."

---

## Architecture Taxonomy

```
                    Multi-Agent Systems
                           │
              ┌────────────┼────────────┐
              │                         │
        Collaborative               Competitive
              │                         │
     ┌────────┼────────┐         ┌──────┼──────┐
     │        │        │         │             │
Hierarchical Flat   Pipeline   Debate      Auction
(Supervisor) (Swarm) (Chain)  (Adversarial) (Market)
```

---

## Architecture 1: Hierarchical (Supervisor)

```
              ┌──────────────┐
              │  SUPERVISOR   │
              │  (orchestrates│
              │   + decides)  │
              └──────┬───────┘
           ┌─────────┼──────────┐
           ▼         ▼          ▼
     ┌──────────┐┌──────────┐┌──────────┐
     │ Agent A  ││ Agent B  ││ Agent C  │
     │(Research)││(Analysis)││(Writing) │
     └──────────┘└──────────┘└──────────┘
```

| Aspect | Details |
|---|---|
| **Decision making** | Centralized — supervisor routes all tasks |
| **Communication** | Hub-and-spoke (all through supervisor) |
| **Pros** | Clear control, easy to debug, predictable |
| **Cons** | Supervisor is a bottleneck, single point of failure |
| **Best for** | Enterprise workflows, regulated industries |

---

## Architecture 2: Flat / Peer-to-Peer

```
     ┌──────────┐     ┌──────────┐
     │ Agent A  │◀───▶│ Agent B  │
     └────┬─────┘     └────┬─────┘
          │                │
          │   ┌──────────┐ │
          └──▶│ Agent C  │◀┘
              └──────────┘
```

| Aspect | Details |
|---|---|
| **Decision making** | Distributed — agents negotiate/vote |
| **Communication** | Peer-to-peer (any agent can message any other) |
| **Pros** | No bottleneck, resilient to single agent failure |
| **Cons** | Hard to coordinate, potential deadlocks, harder to debug |
| **Best for** | Research, creative tasks, brainstorming |

---

## Architecture 3: Pipeline (Sequential)

```
Input → [Agent A] → [Agent B] → [Agent C] → Output
         (Fetch)     (Process)    (Format)
```

| Aspect | Details |
|---|---|
| **Decision making** | Predefined order — no dynamic routing |
| **Communication** | Pass-forward only |
| **Pros** | Simple, predictable, easy to test each stage |
| **Cons** | No parallelism, one failure blocks all downstream |
| **Best for** | ETL-style workflows, content pipelines |

---

## Architecture 4: Blackboard

```
┌─────────────────────────────────┐
│         BLACKBOARD              │
│  (shared knowledge space)       │
│                                 │
│  Facts:    [fact1, fact2, ...]  │
│  Status:   [step1: done, ...]  │
│  Pending:  [task3, task4, ...] │
└───────┬────────┬────────┬──────┘
        │        │        │
   ┌────▼──┐ ┌──▼────┐ ┌─▼──────┐
   │Agent A│ │Agent B│ │Agent C │
   │(reads/│ │(reads/│ │(reads/ │
   │writes)│ │writes)│ │writes) │
   └───────┘ └───────┘ └────────┘
```

| Aspect | Details |
|---|---|
| **Decision making** | Agents independently check and contribute |
| **Communication** | Through shared state (the "blackboard") |
| **Pros** | Flexible, agents can work independently |
| **Cons** | Coordination complexity, race conditions |
| **Best for** | Complex problem solving, scientific discovery |

---

## Architecture 5: Market / Auction

```
Task Pool: [Task A, Task B, Task C]
    │
    ▼
Agents bid on tasks:
  Agent 1: "I can do Task A for 500 tokens"
  Agent 2: "I can do Task A for 300 tokens"  ← Winner
  Agent 3: "I can do Task B for 200 tokens"  ← Winner
```

| Aspect | Details |
|---|---|
| **Decision making** | Market-based — agents bid for tasks |
| **Communication** | Through auction/bidding system |
| **Pros** | Optimal resource allocation, self-organizing |
| **Cons** | Complex to implement, unpredictable behavior |
| **Best for** | Resource-constrained systems, research |

---

## Choosing an Architecture

| If your system needs... | Choose... |
|---|---|
| Clear control and auditability | **Hierarchical** |
| Resilience and no bottleneck | **Flat / P2P** |
| Simple sequential processing | **Pipeline** |
| Flexible, independent contribution | **Blackboard** |
| Optimal resource allocation | **Market** |
| Quick prototype | **Pipeline** (simplest) |
| Enterprise production | **Hierarchical** (most common) |

---

## Architecture Diagram: Enterprise Multi-Agent System

```
┌──────────────────────────────────────────────────────────┐
│                    API GATEWAY                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              SUPERVISOR AGENT                       │  │
│  │  - Task routing                                    │  │
│  │  - State management                               │  │
│  │  - Result aggregation                             │  │
│  │  - Error handling                                 │  │
│  └──────────────────┬─────────────────────────────────┘  │
│         ┌───────────┼───────────┬──────────┐            │
│         ▼           ▼           ▼          ▼            │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐      │
│  │ Research │ │ Analysis │ │ Code   │ │ Review │      │
│  │  Agent   │ │  Agent   │ │ Agent  │ │ Agent  │      │
│  │          │ │          │ │        │ │        │      │
│  │ Tools:   │ │ Tools:   │ │ Tools: │ │ Tools: │      │
│  │ -search  │ │ -python  │ │ -exec  │ │ -lint  │      │
│  │ -scrape  │ │ -sql     │ │ -git   │ │ -test  │      │
│  │ -read    │ │ -chart   │ │ -write │ │ -scan  │      │
│  └──────────┘ └──────────┘ └────────┘ └────────┘      │
│         │           │           │          │            │
│  ┌──────┴───────────┴───────────┴──────────┴────────┐  │
│  │              SHARED STATE (Redis)                 │  │
│  │  - Task status                                   │  │
│  │  - Intermediate results                          │  │
│  │  - Agent communication channels                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  INFRASTRUCTURE: Temporal + K8s + Postgres + S3   │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## Interview Questions They Will Ask

1. **"Design a multi-agent system for [X]."**
   → Start with: what agents are needed? How do they communicate? Who orchestrates? What's the failure handling? Draw the architecture.

2. **"Hierarchical vs flat multi-agent systems — trade-offs?"**
   → Hierarchical: clear control, easy debug, but bottleneck risk. Flat: resilient, no bottleneck, but coordination is hard and debugging is a nightmare.

3. **"How do agents share state?"**
   → Shared store (Redis), message passing, or blackboard. Choice depends on consistency needs (strong → DB, eventual → messages).

4. **"What happens when one agent fails?"**
   → Supervisor retries or reassigns. Circuit breaker prevents cascade. Completed work is persisted (checkpointed). Partial results can be useful.

5. **"How do you prevent agents from doing redundant work?"**
   → Task deduplication in the shared state, clear role boundaries, supervisor tracks who is doing what.

---

## Common Mistakes

⚠️ **Starting with multi-agent when single agent suffices** — Multi-agent adds complexity. Use only when a single agent genuinely can't handle the task.

⚠️ **No clear ownership** — Each task should be owned by exactly one agent at a time. Shared ownership = confusion.

⚠️ **Synchronous coordination** — Agents waiting on each other creates bottlenecks. Use async where possible.

⚠️ **No shared state management** — Without proper state management, agents lose track of what's been done.

⚠️ **Overcomplicating the architecture** — Start with hierarchical (supervisor + 2-3 workers). Add complexity only when needed.

---

## TL;DR

- Five architectures: **Hierarchical, Flat, Pipeline, Blackboard, Market**
- **Hierarchical (supervisor)** is the most common in production
- Choose based on: **control needs, failure tolerance, complexity, auditability**
- **Shared state** (Redis/DB) is essential for coordination
- Start simple — **add agents and complexity only when justified**
