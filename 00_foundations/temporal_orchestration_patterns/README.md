# Temporal Orchestration Patterns

## What This Covers

Coordinating multi-step ML workflows that run over time.


## Key Concepts

- Workflow engines: managing long-running, stateful pipelines
- DAG-based orchestration: defining task dependencies and execution order
- Idempotency and checkpointing for safe retries and resumption


## Core Components

- Task DAGs for training, evaluation, and deployment pipelines
- Event-driven triggers: schedule-based, data-arrival, drift-detected
- Checkpointing to resume failed workflows without re-running everything
- State management for multi-step agent and chain executions
- Concurrency control: parallelism limits, resource locks, rate limiting


## Key Trade-offs

- Fully orchestrated pipelines (reliable) vs ad-hoc scripts (fast to build)
- Fine-grained tasks for restartability vs coarse tasks for simplicity
- Central orchestrator (visibility) vs choreography (loose coupling)


## Must Explain in Interview

- Why ML pipelines need orchestration beyond a cron job
- How checkpointing enables cost-efficient recovery from mid-pipeline failures
- The difference between orchestration and choreography and when to pick each
- How to handle idempotency when a training step is retried
- How event-driven triggers reduce unnecessary pipeline runs
