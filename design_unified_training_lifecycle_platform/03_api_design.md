# 3. API Design

> All endpoints are FastAPI. Request/response bodies are Pydantic models.
> Validation happens at the API layer — bad requests never reach Temporal.


## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/jobs` | Submit a new job |
| `GET` | `/jobs/{id}` | Get job status + metadata |
| `GET` | `/jobs` | List jobs (filter by project, type, status) |
| `POST` | `/jobs/{id}/cancel` | Cancel a running/queued job |
| `POST` | `/jobs/{id}/pause` | Pause a running job (checkpoint first) |
| `POST` | `/jobs/{id}/resume` | Resume a paused job from checkpoint |
| `POST` | `/jobs/{id}/priority` | Change job priority |
| `GET` | `/models` | List models (filter by project, stage) |
| `GET` | `/models/{id}` | Get model details + lineage |
| `POST` | `/models/{id}/promote` | Promote model to next stage |
| `POST` | `/models/{id}/rollback` | Rollback to previous model version |


## Core Pydantic Models

### JobSpec (submission payload)

```json
{
  "org_id": "acme",
  "project_id": "chatbot-v2",
  "idempotency_key": "ft-chatbot-v2-2024-run-3",
  "job_type": "fine_tune",

  "data_refs": {
    "dataset_id": "ds-abc123",
    "dataset_version": "v3",
    "format": "instruction"
  },

  "model_ref": {
    "base_model": "llama-3-8b",
    "base_version": "v1.0"
  },

  "method_config": {
    "method": "lora",
    "lora_rank": 16,
    "learning_rate": 2e-4,
    "epochs": 3,
    "batch_size": 8
  },

  "resource_spec": {
    "gpu_type": "A100",
    "gpu_count": 4,
    "spot_ok": true
  },

  "policies": {
    "max_runtime_hours": 24,
    "checkpoint_interval_min": 30,
    "retry_max": 3,
    "timeout_per_activity_sec": 7200
  },

  "eval_policy": {
    "benchmarks": ["mmlu", "human_eval"],
    "min_scores": {"mmlu": 0.75},
    "auto_promote": false
  },

  "tags": {"team": "nlp", "experiment": "lora-rank-sweep"}
}
```

WHY every field:
- `idempotency_key`: prevents duplicate jobs on retry
- `data_refs` with version: reproducibility + lineage
- `method_config`: Strategy pattern — method determines training code path
- `resource_spec`: scheduler uses this for bin-packing + quota check
- `policies`: Temporal uses these for retry/timeout/heartbeat config
- `eval_policy`: gates promotion — no silent bad models in prod


### HPO-specific extension

```json
{
  "job_type": "hpo",
  "hpo_config": {
    "search_strategy": "bayesian",
    "max_trials": 50,
    "param_space": {
      "learning_rate": {"type": "log_uniform", "low": 1e-5, "high": 1e-3},
      "lora_rank": {"type": "categorical", "values": [8, 16, 32]}
    },
    "pruning": {
      "strategy": "median",
      "min_steps_before_prune": 100
    },
    "objective_metric": "eval_loss",
    "direction": "minimize"
  }
}
```

WHY: HPO needs param space + pruning config at submission time to control cost.


### RLHF-specific extension

```json
{
  "job_type": "rlhf",
  "rlhf_config": {
    "preference_dataset_ref": "ds-pref-456-v2",
    "alignment_method": "dpo",
    "reward_model_ref": "rm-789-v1",
    "safety_benchmarks": ["toxigen", "bias_bench"],
    "safety_thresholds": {"toxigen": 0.05}
  }
}
```

WHY: RLHF has its own data format (preference pairs), method (PPO vs DPO), and safety gates.


### Job Response

```json
{
  "job_id": "job-20240115-abc",
  "status": "running",
  "job_type": "fine_tune",
  "project_id": "chatbot-v2",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "temporal_workflow_id": "wf-ft-abc123",
  "progress": {
    "current_epoch": 2,
    "total_epochs": 3,
    "current_step": 4500,
    "last_checkpoint": "s3://checkpoints/job-abc/step-4000"
  },
  "resource_usage": {
    "gpu_hours_used": 3.5,
    "gpu_hours_budget": 24.0
  }
}
```


## Validation & Error Cases

### At submission time (synchronous, < 200ms):

| Check | Error | HTTP |
|---|---|---|
| Schema validation fails | `422 Validation Error` with field details | 422 |
| Duplicate idempotency_key | `409 Conflict` — return existing job_id | 409 |
| Project quota exceeded | `429 Quota Exceeded` — include remaining budget | 429 |
| Unknown base model | `400 Bad Request` — model not in registry | 400 |
| Dataset version not found | `400 Bad Request` — dataset ref invalid | 400 |
| Unauthorized project | `403 Forbidden` | 403 |

WHY synchronous validation: Fail fast. Don't start Temporal workflows for invalid jobs.

### At runtime (asynchronous, reported via status):

| Failure | Handling |
|---|---|
| GPU preemption | Checkpoint + retry from last checkpoint (Temporal retry) |
| Activity timeout | Temporal retries with backoff |
| Budget exceeded mid-run | Checkpoint + pause + notify team |
| Eval fails thresholds | Block promotion, mark job as `eval_failed` |
| MLflow unreachable | Retry with backoff; compensate if still down |


## Promote Model

```
POST /models/{id}/promote
```

```json
{
  "target_stage": "staging",
  "approval_ref": "approval-789",
  "rollout_strategy": "canary",
  "canary_percent": 10
}
```

- WHY `approval_ref`: links to approval workflow for compliance audit trail.
- WHY `rollout_strategy`: safe promotion requires canary/shadow, not instant swap.


## TL;DR (Interview Summary)

- One `POST /jobs` endpoint handles all 5 job types via Pydantic discriminated union
- JobSpec carries everything: data refs, model refs, method config, resource spec, policies
- Idempotency key on every submission — 409 on duplicate, return existing job
- Synchronous validation (schema + quota + refs) — fail fast, never waste GPUs
- HPO config includes param space + pruning — cost control at submission time
- RLHF config includes preference refs + safety thresholds — alignment gates built in
- Promote endpoint requires approval ref + rollout strategy — compliance by design
- All runtime failures reported via job status polling (or webhooks)
