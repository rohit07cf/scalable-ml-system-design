# Design: Agentic Workflow Engine (Temporal-style)

Design a durable execution engine for LLM-powered agentic workflows that survives crashes, supports long-running tasks, and provides replay and observability.


## Key Requirements

- Workflows must survive process restarts without losing progress (durable execution)
- Support branching, parallel fan-out, human wait steps, and conditional retries
- Full deterministic replay for debugging and auditability


## Core Components

- **Workflow Definition Layer** -- DSL or code-based DAG that defines steps, transitions, and compensation logic
- **Durable State Store** -- event-sourced log of every step outcome, enabling replay (e.g., Temporal history)
- **Activity Workers** -- stateless executors that run individual steps (LLM calls, tool invocations, API calls)
- **Scheduler / Timer Service** -- manages delays, timeouts, cron triggers, and human-wait deadlines
- **Replay Engine** -- re-executes workflow code against stored history for recovery and debugging


## Key Trade-offs

- Event-sourced replay (strong auditability) vs. checkpoint-based recovery (simpler, less storage)
- Deterministic workflow code constraint (safe replay) vs. flexible non-deterministic logic (harder to replay)
- Single workflow queue (simple) vs. priority-based routing (better SLAs, more operational complexity)


## Must Explain in Interview

- How deterministic replay works and why workflow code must be side-effect-free
- How you handle LLM calls as activities (non-deterministic outputs stored, not re-executed on replay)
- How timeouts and heartbeats detect stuck activities and trigger compensation
- How you version workflow definitions without breaking in-flight executions
- How you set concurrency limits and backpressure to control LLM cost during fan-out
