# Design: Human-in-the-Loop State Management

Design a system that pauses agentic workflows at defined checkpoints for human review or approval, preserving full execution state across potentially long wait times.


## Key Requirements

- Workflows pause cleanly at approval gates without holding compute resources
- State is durable across hours or days of human wait time
- Humans can approve, reject, edit agent outputs, or reroute execution


## Core Components

- **Checkpoint Manager** -- serializes full execution state (context, partial results, pending actions) at gate points
- **Approval Queue** -- priority-ordered work queue surfaced to human reviewers with SLA tracking
- **State Store** -- persistent store for paused workflow snapshots (e.g., DynamoDB, Postgres with JSONB)
- **Resume Controller** -- validates human input, rehydrates state, and restarts the workflow from the gate
- **Escalation Engine** -- auto-escalates if human response exceeds SLA, supports delegation rules


## Key Trade-offs

- Synchronous wait (simpler, wastes resources) vs. async checkpoint-resume (efficient, more complex rehydration)
- Full state serialization (safe, large payloads) vs. reference-based state (smaller, risk of stale references)
- Strict approval gates (safer, slower) vs. confidence-based auto-approve (faster, requires good calibration)


## Must Explain in Interview

- How you serialize and rehydrate agent state without losing context window or tool call history
- How you handle state schema evolution when workflows are paused across a deployment
- How the escalation SLA timer works and what happens on timeout (auto-approve, reject, or re-route)
- How you prevent race conditions when multiple reviewers act on the same checkpoint
- How you audit every human decision and feed approvals/rejections back for model improvement
