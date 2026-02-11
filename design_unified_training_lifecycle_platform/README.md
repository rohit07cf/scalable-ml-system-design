# Design: Single-Org Enterprise LLM Training & Lifecycle Platform

## Interview Pitch (10 lines, spoken style)

> "We're building an internal ML platform that unifies all training lifecycle
> use cases — fine-tuning, hyperparameter optimization, continuous retraining,
> and RLHF alignment — behind one self-serve API. The control plane is
> Python/FastAPI with Pydantic-validated job specs. Temporal orchestrates every
> workflow durably — retries, heartbeats, timeouts, child-workflow fanout for
> HPO trials. Kubernetes runs the actual compute across separate CPU and GPU
> worker pools with namespace isolation per project. Storage flows from S3
> through PVCs for fast local I/O and back to S3 + MLflow for durability and
> lineage. Cost governance is baked in: GPU-hour budgets, HPO pruning,
> priority queues, and fairness quotas. The result is a platform where any
> internal team can submit a typed job and get a production-ready model with
> full lineage, eval gating, and safe rollout."


## System Scope (8 bullets)

- Unified job API for fine-tune, HPO, retrain, RLHF, eval-only
- Pydantic-validated schemas with idempotency + quota checks
- Temporal-orchestrated durable workflows with per-type routing
- Kubernetes CPU/GPU worker pools with autoscaling + isolation
- Checkpoint-based resume for spot/preemption resilience
- Offline eval + safety gating before any model promotion
- MLflow registry with staged promotion + rollback
- Cost governance: budgets, quotas, priorities, HPO pruning


## Key Components

| Component | Role |
|---|---|
| **API Gateway** | FastAPI control plane, validation, auth |
| **Job Scheduler** | Quota check, priority queue, Temporal dispatch |
| **Temporal Server** | Durable workflow orchestration |
| **CPU Workers** | Validation, preprocessing, packaging, uploads |
| **GPU Workers** | Training, eval, reward model, alignment |
| **Storage Layer** | S3 (durable) + PVC (fast) + MLflow (registry) |
| **Eval & Safety** | Offline benchmarks, safety checks, approval gates |
| **Monitoring** | Drift detection, cost tracking, alerting |


## How to Present in 8 Minutes

1. **[0:00–1:00]** State requirements — functional + non-functional (01)
2. **[1:00–1:30]** Quick estimation — jobs, GPU hours, storage (02)
3. **[1:30–2:30]** API surface — key endpoints + Pydantic models (03)
4. **[2:30–5:00]** HLD — draw the ASCII diagram, walk data flows (04)
5. **[5:00–5:30]** DB schema — key tables, indexing strategy (05)
6. **[5:30–7:00]** Deep dives — state machine, retries, checkpointing (06)
7. **[7:00–8:00]** Wrap up — bottlenecks, scaling, trade-offs (07)

> Tip: Draw the diagram FIRST, then narrate the flow through it.


## File Index

| # | File | Phase |
|---|---|---|
| 1 | [01_requirements.md](01_requirements.md) | Requirements |
| 2 | [02_estimation.md](02_estimation.md) | Estimation |
| 3 | [03_api_design.md](03_api_design.md) | API Design |
| 4 | [04_hld.md](04_hld.md) | High-Level Design |
| 5 | [05_db_design.md](05_db_design.md) | Database Design |
| 6 | [06_deep_dives.md](06_deep_dives.md) | Deep Dives |
| 7 | [07_wrap_up.md](07_wrap_up.md) | Wrap Up |


## TL;DR (Interview Summary)

- Single API + Pydantic validation for all job types (fine-tune, HPO, retrain, RLHF)
- Temporal orchestrates every workflow; Factory routes job_type to workflow + queue + retry profile
- CPU_TASK_QUEUE for cheap work, GPU_TASK_QUEUE for training — never waste GPUs on validation
- Kubernetes namespaces + RBAC for project isolation; taints/tolerations for GPU scheduling
- S3 -> PVC -> run -> PVC -> S3 storage lifecycle; checksums + idempotent uploads
- MLflow registry with staged promotion (dev -> staging -> prod) + eval gating
- Cost governance at every layer: budgets, quotas, HPO pruning, spot policies
- Failure-resilient: checkpoint resume, heartbeats, idempotent retries, compensation steps
