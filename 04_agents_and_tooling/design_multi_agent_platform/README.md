# Design: Multi-Agent Platform

Design a platform where multiple LLM-backed agents collaborate to complete complex tasks, with clear delegation, communication, and observability.


## Key Requirements

- Agents must be independently deployable with well-defined capability boundaries
- Orchestrator routes subtasks, merges results, and handles partial failures
- Full trace of every agent invocation, tool call, and delegation decision


## Core Components

- **Agent Registry** -- catalog of available agents, their capabilities, input/output schemas
- **Orchestrator** -- decomposes user intent into subtasks, assigns to agents, manages execution DAG
- **Message Bus** -- async communication layer between agents (e.g., NATS, Kafka, or in-process queue)
- **Shared Context Store** -- scoped key-value store agents read/write during a session
- **Observability Collector** -- traces, token counts, latency, and cost per agent per step


## Key Trade-offs

- Central orchestrator (simpler debugging) vs. peer-to-peer agent communication (lower latency, harder to trace)
- Shared context (easier coordination) vs. isolated context (better fault isolation, weaker coherence)
- Static task decomposition (predictable) vs. dynamic re-planning (adaptive but harder to bound cost and latency)


## Must Explain in Interview

- How the orchestrator decides which agent handles a subtask (capability matching, routing policy)
- How you prevent infinite delegation loops and bound total cost per request
- How shared context is scoped and garbage-collected across multi-turn sessions
- What happens when one agent in the DAG fails (retry, fallback, partial result propagation)
- How you version agents independently without breaking orchestration contracts
