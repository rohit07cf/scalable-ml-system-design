# 5. Database Design

> Postgres for all metadata. S3 for blobs. MLflow for model registry.
> DB is the source of truth for job state; Temporal is source of truth for workflow state.


## Tables Overview

```
Jobs ──1:N──> Runs ──1:N──> Artifacts
  │                │
  │                └──1:N──> Metrics
  │
  └──N:1──> Projects ──1:1──> Quotas
                │
                └──1:N──> Models ──1:N──> ModelVersions
                                            │
                                            └──1:N──> Approvals
```


## Table: `jobs`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | Server-generated |
| `idempotency_key` | VARCHAR (UNIQUE) | Client-provided dedupe key |
| `project_id` | VARCHAR (FK) | Links to project/team |
| `org_id` | VARCHAR | Single org, but future-proofs |
| `job_type` | ENUM | fine_tune, hpo, retrain, rlhf, eval_only |
| `status` | ENUM | submitted, queued, running, paused, completed, failed, cancelled, eval_failed |
| `priority` | INT | Higher = more urgent (default 5) |
| `config_json` | JSONB | Full JobSpec snapshot (immutable after submit) |
| `temporal_workflow_id` | VARCHAR | Link to Temporal workflow |
| `parent_job_id` | UUID (FK, nullable) | For HPO trials -> parent HPO job |
| `created_at` | TIMESTAMP | Submission time |
| `updated_at` | TIMESTAMP | Last status change |
| `started_at` | TIMESTAMP (nullable) | When training began |
| `completed_at` | TIMESTAMP (nullable) | When job finished |
| `error_message` | TEXT (nullable) | Failure details |
| `tags` | JSONB | Freeform metadata |

WHY `config_json` as JSONB: Preserves exact config for reproducibility. JSONB allows querying.
WHY `parent_job_id`: Links HPO trials to their parent sweep.

**Indexes:**
- `UNIQUE(idempotency_key)` — fast dedupe check
- `(project_id, status)` — "show me all running jobs for project X"
- `(status, priority DESC, created_at)` — scheduler queue ordering
- `(job_type, created_at)` — filter by type + time range
- `(created_at)` — time-range scans, partition key

**Partition:** Range-partition by `created_at` (monthly).
WHY: Old jobs are queried less; partition pruning speeds range scans.


## Table: `runs`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `job_id` | UUID (FK) | Parent job |
| `run_number` | INT | Attempt number (1, 2, 3...) |
| `status` | ENUM | running, completed, failed, preempted |
| `started_at` | TIMESTAMP | |
| `completed_at` | TIMESTAMP (nullable) | |
| `gpu_hours_used` | DECIMAL | Actual GPU-hours consumed |
| `last_checkpoint_uri` | VARCHAR | S3 path to last checkpoint |
| `last_checkpoint_step` | INT | Step number of last checkpoint |
| `metrics_json` | JSONB | Final metrics snapshot |
| `worker_node` | VARCHAR | K8s node that ran this |

WHY separate from `jobs`: A job may have multiple runs (retries, preemptions).
WHY `last_checkpoint_uri`: Resume point for next attempt.

**Indexes:**
- `(job_id, run_number)` — get all runs for a job
- `(status)` — find running/preempted runs


## Table: `artifacts`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `run_id` | UUID (FK) | Which run produced this |
| `artifact_type` | ENUM | checkpoint, model, adapter, log, eval_report |
| `storage_uri` | VARCHAR | S3 path |
| `checksum_sha256` | VARCHAR | Integrity verification |
| `size_bytes` | BIGINT | For storage accounting |
| `created_at` | TIMESTAMP | |
| `metadata_json` | JSONB | Step number, epoch, etc. |

WHY checksums: Detect corrupt uploads. Idempotent re-upload check.
WHY `artifact_type`: Different retention policies per type (checkpoints expire, models don't).

**Indexes:**
- `(run_id, artifact_type)` — get all checkpoints for a run
- `(created_at)` — retention policy cleanup scans


## Table: `models`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `project_id` | VARCHAR (FK) | Owning project |
| `model_name` | VARCHAR | Human-readable name |
| `base_model_ref` | VARCHAR | e.g., "llama-3-8b" |
| `created_at` | TIMESTAMP | |

**Indexes:**
- `(project_id, model_name)` — find model by project


## Table: `model_versions`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `model_id` | UUID (FK) | Parent model |
| `version_number` | INT | Auto-increment per model |
| `stage` | ENUM | dev, staging, prod, archived |
| `job_id` | UUID (FK) | Which job produced this version |
| `run_id` | UUID (FK) | Which run specifically |
| `artifact_uri` | VARCHAR | S3 path to model files |
| `dataset_version` | VARCHAR | Exact dataset version used |
| `config_hash` | VARCHAR | Hash of training config |
| `code_commit` | VARCHAR | Git commit SHA |
| `mlflow_run_id` | VARCHAR | Cross-reference to MLflow |
| `eval_metrics_json` | JSONB | Eval scores at promotion time |
| `created_at` | TIMESTAMP | |
| `promoted_at` | TIMESTAMP (nullable) | When moved to current stage |
| `promoted_by` | VARCHAR (nullable) | User or system that promoted |

WHY full lineage columns: Audit requires tracing model -> data + code + config.
WHY `config_hash`: Fast comparison without storing full config again.

**Indexes:**
- `(model_id, stage)` — "what's the current prod version of model X?"
- `(model_id, version_number DESC)` — latest version


## Table: `projects`

| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR (PK) | e.g., "chatbot-v2" |
| `org_id` | VARCHAR | Owning org |
| `display_name` | VARCHAR | |
| `k8s_namespace` | VARCHAR | Mapped K8s namespace |
| `created_at` | TIMESTAMP | |
| `owner` | VARCHAR | Team lead / contact |

WHY `k8s_namespace`: Direct mapping enables namespace-level RBAC + ResourceQuota.


## Table: `quotas`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `project_id` | VARCHAR (FK, UNIQUE) | One quota per project |
| `gpu_hours_budget` | DECIMAL | Monthly GPU-hour limit |
| `gpu_hours_used` | DECIMAL | Running total this period |
| `max_concurrent_jobs` | INT | Max simultaneous running jobs |
| `current_concurrent` | INT | Current count |
| `priority_tier` | INT | Default priority for this project |
| `period_start` | DATE | Budget period start |
| `period_end` | DATE | Budget period end |

WHY `gpu_hours_used` as running total: Fast check at submission time.
Atomicity: Use `UPDATE ... SET gpu_hours_used = gpu_hours_used + delta WHERE gpu_hours_used + delta <= gpu_hours_budget` for atomic budget check.

**Indexes:**
- `UNIQUE(project_id)` — one quota per project


## Table: `approvals`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | |
| `model_version_id` | UUID (FK) | Which version needs approval |
| `requested_by` | VARCHAR | User who triggered promotion |
| `approved_by` | VARCHAR (nullable) | Approver |
| `status` | ENUM | pending, approved, rejected |
| `target_stage` | ENUM | staging, prod |
| `eval_snapshot_json` | JSONB | Eval metrics at request time |
| `requested_at` | TIMESTAMP | |
| `decided_at` | TIMESTAMP (nullable) | |
| `reason` | TEXT (nullable) | Approval/rejection reason |

WHY immutable `eval_snapshot_json`: Approver sees exact metrics that triggered the request.

**Indexes:**
- `(status, requested_at)` — pending approvals queue
- `(model_version_id)` — approvals for a specific version


## Read Path vs Write Path

### Write Path (hot)
- Job submission: INSERT into `jobs` + UPDATE `quotas` (atomic)
- Status updates: UPDATE `jobs.status` (frequent during run)
- Checkpoint logging: INSERT into `artifacts`
- Metrics logging: UPDATE `runs.metrics_json`
- Budget accounting: UPDATE `quotas.gpu_hours_used`

### Read Path (hot)
- Job status polling: SELECT from `jobs` by ID (indexed PK)
- Project dashboard: SELECT from `jobs` WHERE project_id + status (composite index)
- Scheduler queue: SELECT from `jobs` WHERE status=queued ORDER BY priority, created_at (composite index)
- Model lookup: SELECT from `model_versions` WHERE model_id + stage (composite index)

### Read Path (cold)
- Audit queries: Scan `jobs` + `model_versions` by time range (partition pruning)
- Lineage queries: Join `model_versions` -> `runs` -> `artifacts` (FK-indexed joins)

WHY separate hot/cold: Partition pruning keeps hot queries fast. Cold queries tolerate latency.


## Common Interview Mistakes to Avoid

- **No lineage linking**: Model without a link to dataset version + config + code = useless for audit.
  FIX: `model_versions` has explicit `dataset_version`, `config_hash`, `code_commit` columns.

- **Storing blobs in DB**: Checkpoints can be 20+ GB. Never store in Postgres.
  FIX: DB stores URIs; blobs live in S3.

- **No idempotency_key**: Without it, retried submissions create duplicate jobs.
  FIX: UNIQUE constraint on `idempotency_key` + 409 on conflict.

- **Single-row quota check**: Race condition if two jobs check budget simultaneously.
  FIX: Atomic UPDATE with WHERE clause `gpu_hours_used + delta <= budget`.

- **No partitioning**: Jobs table grows forever; scans get slow.
  FIX: Range-partition by `created_at` (monthly).

- **Missing parent_job_id**: HPO trials not linked to parent sweep.
  FIX: `parent_job_id` column makes HPO hierarchy queryable.


## TL;DR (Interview Summary)

- 7 tables: Jobs, Runs, Artifacts, Models, ModelVersions, Quotas, Approvals
- Jobs partitioned by `created_at` (monthly) — keeps scans fast
- Lineage is explicit columns, not hidden in JSONB — auditable by design
- Blobs in S3, URIs + checksums in DB — never store 20 GB checkpoints in Postgres
- Atomic budget check via UPDATE WHERE clause — no race conditions
- Idempotency key is UNIQUE — duplicate submissions return 409
- Parent-child linking for HPO trials via `parent_job_id`
- Read path is index-covered; write path is single-row updates
