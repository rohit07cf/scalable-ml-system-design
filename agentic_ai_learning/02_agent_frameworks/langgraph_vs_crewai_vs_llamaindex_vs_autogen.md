# Agent Frameworks Comparison

## What It Is

- **Agent frameworks** = libraries/platforms that provide the scaffolding to build AI agents
- They handle the boilerplate: reasoning loops, tool integration, memory, multi-agent orchestration
- Choosing the right framework is a key architectural decision
- The landscape is evolving fast — what matters is understanding the **design philosophy** of each

## Why It Matters (Interview Framing)

> "Interviewers don't care if you memorized API docs. They want to know: given requirements X, why would you pick framework A over B? What are the trade-offs? Can you justify your choice architecturally?"

---

## The Big Comparison Table

| Feature | **LangGraph** | **CrewAI** | **LlamaIndex Agents** | **AutoGen** | **OpenAI Agents SDK** | **MS Agent Framework** |
|---|---|---|---|---|---|---|
| **By** | LangChain | CrewAI Inc | LlamaIndex | Microsoft | OpenAI | Microsoft |
| **Philosophy** | Graph-based workflows | Role-based crews | Data-centric agents | Multi-agent conversations | Minimal, production-first | Enterprise integration |
| **Execution Model** | State machine (DAG) | Sequential/hierarchical | Pipeline + agent loops | Async message passing | Handoff-based loops | Pluggable orchestrators |
| **State Management** | First-class (checkpoints, persistence) | Basic (shared memory) | Context-based | Conversation history | Context variables | Dependency injection |
| **Multi-Agent** | Explicit graph nodes | Crew of role-assigned agents | Orchestrator pattern | Group chat / nested | Agent handoffs | Multi-agent via DI |
| **Tool Integration** | LangChain tools + custom | Custom tools, decorators | LlamaIndex tools | Function calling | Python functions | Plugin system |
| **Memory** | Built-in (short + long-term) | Shared crew memory | Index-based (RAG-native) | Chat history | Thread-based | External stores |
| **Streaming** | Yes | Limited | Yes | Yes | Yes | Yes |
| **Human-in-the-Loop** | Built-in interrupt/resume | Callback-based | Manual | Built-in | Built-in | Configurable |
| **Production Ready** | High | Medium | Medium | Medium | High | Medium-High |
| **Learning Curve** | Steep (graph concepts) | Low (intuitive API) | Medium | Medium | Low | Medium |
| **Best For** | Complex stateful workflows | Quick multi-agent prototypes | RAG-heavy agent apps | Research, experimentation | Production OpenAI agents | Enterprise .NET/Python |

---

## Framework Deep Dives

### LangGraph

```
┌──────┐    ┌──────┐    ┌──────┐
│Node A│───▶│Node B│───▶│Node C│
│(plan)│    │(exec)│    │(eval)│
└──────┘    └──┬───┘    └──────┘
               │              │
               └── conditional ──▶ back to Node A
                   edge
```

**Key concepts:**
- **Nodes** = agent steps (functions)
- **Edges** = transitions (conditional or fixed)
- **State** = typed dict passed between nodes, persisted to checkpoints
- **Checkpoints** = save/resume execution at any point

**Strengths:**
- Most control over agent behavior
- Built-in persistence (Postgres, SQLite)
- Human-in-the-loop with interrupt/resume
- Production-grade (LangSmith integration)

**Weaknesses:**
- Steep learning curve
- Verbose for simple agents
- Tightly coupled to LangChain ecosystem

**Use when:** Complex, stateful, production workflows with branching logic.

---

### CrewAI

```
┌─────────────────────────────┐
│           CREW               │
│                             │
│  ┌──────────┐ ┌──────────┐ │
│  │Researcher│ │  Writer   │ │
│  │  Agent   │ │  Agent    │ │
│  │(role,    │ │(role,     │ │
│  │ goal,    │ │ goal,     │ │
│  │ tools)   │ │ tools)    │ │
│  └────┬─────┘ └────┬─────┘ │
│       │             │       │
│       └──────┬──────┘       │
│              ▼              │
│       ┌──────────┐          │
│       │  Process │          │
│       │(sequential│         │
│       │/hierarch.)│         │
│       └──────────┘          │
└─────────────────────────────┘
```

**Key concepts:**
- **Agents** = defined by role, goal, backstory
- **Tasks** = work items assigned to agents
- **Crew** = collection of agents + tasks + process
- **Process** = execution strategy (sequential, hierarchical)

**Strengths:**
- Intuitive mental model (think: team of specialists)
- Quick to prototype
- Good for multi-agent scenarios
- Clean API

**Weaknesses:**
- Limited state management
- Less control over execution flow
- Newer, evolving fast
- Production tooling still maturing

**Use when:** Multi-agent scenarios where role assignment is natural (research team, content pipeline).

---

### LlamaIndex Agents

**Key concepts:**
- Built on LlamaIndex's data framework
- Agents that are **natively good at RAG** — querying indices, combining data sources
- Supports ReAct, OpenAI function calling, and custom agent loops
- Strong at structured + unstructured data retrieval

**Strengths:**
- Best-in-class RAG integration
- Natural for data-heavy agent tasks
- Good abstractions for query pipelines
- Composable agent architectures

**Weaknesses:**
- Less focus on multi-agent orchestration
- RAG-centric — may feel forced for non-data tasks
- Smaller community than LangChain

**Use when:** Your agent's primary job is querying, analyzing, or synthesizing data from multiple sources.

---

### Microsoft AutoGen

```
┌──────────┐  message  ┌──────────┐
│ Agent A   │─────────▶│ Agent B   │
│(assistant)│◀─────────│ (user     │
│           │  message  │  proxy)   │
└──────────┘           └──────────┘
```

**Key concepts:**
- **Conversable agents** that communicate via messages
- **Group chat** for multi-agent discussions
- **Nested conversations** for complex workflows
- Strong support for code generation + execution

**Strengths:**
- Flexible multi-agent conversations
- Good for code generation workflows
- Supports human-agent collaboration
- Active Microsoft Research backing

**Weaknesses:**
- Can be unpredictable (agents "talking" endlessly)
- State management is conversation-based (hard to persist)
- Production readiness still evolving

**Use when:** Research, experimentation, code-generation workflows, multi-agent debates.

---

### OpenAI Agents SDK

```
Agent A ──handoff──▶ Agent B ──handoff──▶ Agent C
  │                    │                    │
  └── tools            └── tools            └── tools
```

**Key concepts:**
- **Agents** = lightweight, defined by instructions + tools + handoffs
- **Handoffs** = first-class concept for agent-to-agent delegation
- **Guardrails** = built-in input/output validation
- **Tracing** = built-in observability

**Strengths:**
- Minimal, clean API
- Built-in guardrails and tracing
- Production-focused from day one
- Native OpenAI model integration

**Weaknesses:**
- OpenAI ecosystem lock-in
- Newer (less community content)
- Limited to OpenAI-compatible models (by default)

**Use when:** Building production agents on OpenAI models with clean handoff patterns.

---

### Microsoft Agent Framework

**Key concepts:**
- Enterprise-grade framework for building agents
- Pluggable orchestrators, tools, and memory
- Strong .NET support alongside Python
- Designed for enterprise integration (Azure, M365)

**Strengths:**
- Enterprise features (auth, compliance, telemetry)
- Pluggable architecture
- Azure ecosystem integration
- Multi-language support

**Weaknesses:**
- Heavier setup
- Azure-centric
- Less community-driven

**Use when:** Enterprise environments with Azure infrastructure and .NET teams.

---

## Decision Matrix: Which Framework to Pick

| If your priority is... | Choose... |
|---|---|
| Complex stateful workflows | **LangGraph** |
| Quick multi-agent prototypes | **CrewAI** |
| RAG-heavy data agents | **LlamaIndex Agents** |
| Research / experimentation | **AutoGen** |
| Production OpenAI agents | **OpenAI Agents SDK** |
| Enterprise / Azure integration | **MS Agent Framework** |
| Maximum control + flexibility | **LangGraph** |
| Fastest time to demo | **CrewAI** |

---

## Interview Questions They Will Ask

1. **"Compare LangGraph and CrewAI."**
   → LangGraph = graph-based state machine, max control, steep learning curve. CrewAI = role-based crews, quick to prototype, less control. Pick LangGraph for complex production workflows, CrewAI for rapid multi-agent prototypes.

2. **"When would you NOT use a framework?"**
   → Simple single-agent, single-tool scenarios. The overhead of a framework isn't justified when a basic ReAct loop in 50 lines of code does the job.

3. **"How do you handle state persistence in agent frameworks?"**
   → LangGraph has built-in checkpoints. Others require external stores (Redis, Postgres). State persistence is critical for long-running agents and human-in-the-loop.

4. **"What's your take on the OpenAI Agents SDK?"**
   → Clean, minimal, production-focused. The handoff pattern is elegant for multi-agent systems. Trade-off is OpenAI ecosystem coupling.

5. **"How do you evaluate a new agent framework?"**
   → Execution model, state management, multi-agent support, tool integration, observability, production readiness, community/docs, vendor lock-in.

---

## Common Mistakes

⚠️ **Choosing a framework before understanding the problem** — Start with requirements, then pick the framework. Not the other way around.

⚠️ **Framework lock-in** — Abstract your agent logic from the framework. Make it swappable.

⚠️ **Using a heavy framework for a simple task** — A ReAct loop in 50 lines of Python is often better than importing a full framework.

⚠️ **Ignoring observability** — If the framework doesn't support tracing/logging, you'll be debugging blind.

⚠️ **Comparing frameworks on demo quality** — Demos are designed to impress. Evaluate on: error handling, state recovery, production debugging, and scaling.

---

## TL;DR

- **LangGraph** = most control, graph-based, production-grade, steep learning curve
- **CrewAI** = fastest to prototype, role-based multi-agent, less control
- **LlamaIndex** = best for RAG-heavy agents, data-centric
- **AutoGen** = research-oriented, multi-agent conversations
- **OpenAI SDK** = minimal, production-first, handoff-based, OpenAI-coupled
- Choose based on: **workflow complexity, multi-agent needs, data requirements, production demands**
