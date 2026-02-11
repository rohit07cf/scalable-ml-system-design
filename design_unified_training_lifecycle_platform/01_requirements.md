# 1. Requirements

## Functional Requirements

### Job Submission & Lifecycle

- **Typed job submission** (fine-tune, HPO, retrain, RLHF, eval-only)
  - WHY: Each type has distinct resource needs, workflows, and validation rules.

- **Pydantic schema validation** with strict typing + versioning
  - WHY: Catch bad configs at submission time, not after GPU hours are burned.

- **Idempotent submission keys** (client-generated dedupe key per job)
  - WHY: Network retries must never create duplicate GPU-burning jobs.

- **Cancel / pause / resume / retry-from-checkpoint / priority change**
  - WHY: Training jobs are long-lived; operators need runtime control.

### Data Pipeline

- **Ingest chat/instruction/completion + preference pair formats**
  - WHY: Fine-tune needs instruction data; RLHF needs preference pairs. One ingest path.

- **Dataset validation, dedup, filter, tokenize, version**
  - WHY: Garbage in = garbage out. Versioning links model to exact data for lineage.

### Training & Compute

- **Distributed / multi-GPU training** with preemption-safe checkpointing
  - WHY: Large models need multi-GPU; spot instances need checkpoint resume.

- **HPO fanout** (grid / random / Bayesian) with early stopping / pruning
  - WHY: HPO can explode GPU costs without pruning bad trials early.

- **RLHF pipeline**: preference data -> reward model -> PPO/DPO -> safety validation
  - WHY: Alignment is a multi-stage pipeline, not a single training run.

### Evaluation & Promotion

- **Offline eval + safety checks** before any promotion
  - WHY: Never promote a model that hasn't been benchmarked and safety-checked.

- **Shadow / canary / A-B gates** for safe rollout
  - WHY: Catch regressions in production traffic before full rollout.

- **Approval workflows** for gated promotion (dev -> staging -> prod)
  - WHY: Compliance requires human sign-off on model deployments.

### Registry & Lineage

- **MLflow logging** + model versioning + staged promotion + rollback
  - WHY: Single source of truth for model artifacts, metrics, and lineage.

- **Immutable lineage**: model -> dataset version + code version + config version
  - WHY: Audit/compliance requires full reproducibility chain.

### Retraining

- **Schedule-based or drift/perf-triggered retraining**
  - WHY: Models degrade; automated retraining closes the feedback loop.

- **Safe rollout + rollback** for retrained models
  - WHY: Retrained model might be worse; need safe promotion path.

### Governance

- **Project/team isolation** (namespaces, RBAC)
  - WHY: Teams shouldn't see or affect each other's jobs or data.

- **Fairness quotas, budgets, cost attribution** per project
  - WHY: Shared GPU pool without governance = one team starves others.


## Non-Functional Requirements

### Scale
- Hundreds of jobs/day, ~100–200 concurrent runs
- WHY: Enterprise with multiple teams running diverse workloads daily.

### Reliability
- Temporal retries + timeouts + heartbeats on every activity
- Resumable workflows from last checkpoint on any failure
- WHY: GPU hours are expensive; losing progress is unacceptable.

### Latency
- Control-plane APIs < 200ms p99 (submit, query, cancel)
- WHY: Self-serve UX must feel instant; training latency is separate.

### Availability
- HA control plane (multi-replica FastAPI + Temporal cluster)
- Durable workflow state survives control-plane restarts
- WHY: Platform downtime blocks all teams. Temporal state must survive restarts.

### Cost Controls
- GPU-hour budgets per project, enforced at submission + runtime
- Spot instance policies, HPO pruning, idle GPU reclaim
- WHY: GPUs are the #1 cost driver; unbounded usage breaks budgets.

### Security
- Org-level IAM + project-scoped RBAC
- Encryption at rest + in transit
- Immutable audit trail for all job actions
- WHY: Enterprise compliance requires access control + audit.


## TL;DR (Interview Summary)

- Five job types, one API, strict Pydantic validation at the gate
- Idempotent submissions — never double-spend GPU hours
- Checkpoint-based resume — preemption-safe by design
- Eval + safety gating before every promotion — no blind deployments
- MLflow lineage: model -> data version + config version + code version
- Budget enforcement at submit time AND runtime — cost governance built in
- Project isolation via K8s namespaces + RBAC — multi-team safety
- HA control plane + durable Temporal state — no single point of failure
