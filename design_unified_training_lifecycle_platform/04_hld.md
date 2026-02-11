# 4. High-Level Design (HLD)


## Components

### Control Plane

- **API Gateway (FastAPI)**
  - Pydantic validation, auth, quota check, job CRUD
  - WHY: Single entry point; fail fast before burning resources.

- **Job Scheduler**
  - Priority queue, fairness enforcement, Temporal dispatch
  - WHY: Prevents one team from starving others; routes to correct workflow.

- **Temporal Server (HA cluster)**
  - Durable workflow orchestration, task queues, visibility
  - WHY: Survives crashes; resumes workflows exactly where they left off.

### Data Plane

- **CPU Worker Pool** (Kubernetes, autoscaled)
  - Runs: validation, preprocessing, tokenization, packaging, uploads, metadata
  - Listens on: `CPU_TASK_QUEUE`
  - WHY: Cheap work on cheap nodes; never waste GPU time on data prep.

- **GPU Worker Pool** (Kubernetes, autoscaled, tainted nodes)
  - Runs: fine-tuning, reward model training, PPO/DPO, heavy eval
  - Listens on: `GPU_TASK_QUEUE`
  - WHY: Expensive work on expensive nodes; dedicated scheduling.

### Storage

- **S3** — durable storage for datasets, checkpoints, final models
- **PVC** — fast local NVMe for active training I/O
- **MLflow** — model registry, metric logging, lineage, staged promotion

WHY three layers: S3 for durability, PVC for speed, MLflow for governance.

### Supporting

- **Drift Monitor** — watches production metrics, emits retrain signals
- **Cost Tracker** — aggregates GPU-hours per project, enforces budgets
- **Approval Service** — human-in-the-loop gates for promotion


## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                         │
│                                                          │
│  ┌─────────┐   ┌───────────┐   ┌──────────────────┐     │
│  │ FastAPI  │──>│    Job    │──>│    Temporal       │     │
│  │ Gateway  │   │ Scheduler │   │    Server (HA)    │     │
│  │ +Pydantic│   │ +Quotas   │   │                   │     │
│  └─────────┘   └───────────┘   └────────┬──────────┘     │
│       │                                  │                │
│       │              ┌───────────────────┼──────────┐     │
│       │              │                   │          │     │
│       ▼              ▼                   ▼          │     │
│  ┌─────────┐  ┌─────────────┐  ┌──────────────┐    │     │
│  │  Postgres│  │CPU_TASK_Q   │  │GPU_TASK_Q    │    │     │
│  │  (Jobs,  │  │             │  │              │    │     │
│  │  Meta)   │  └──────┬──────┘  └──────┬───────┘    │     │
│  └─────────┘         │               │              │     │
└──────────────────────┼───────────────┼──────────────┘     │
                       │               │
┌──────────────────────┼───────────────┼──────────────┐
│                 DATA PLANE (K8s)     │              │
│                      │               │              │
│  ┌───────────────────▼──┐  ┌────────▼───────────┐  │
│  │   CPU Workers        │  │   GPU Workers       │  │
│  │   (validate, prep,   │  │   (train, eval,     │  │
│  │    tokenize, upload) │  │    RLHF, reward)    │  │
│  └──────────┬───────────┘  └────────┬────────────┘  │
│             │                       │               │
│             └───────────┬───────────┘               │
│                         │                           │
│                         ▼                           │
│  ┌─────────────────────────────────────────────┐    │
│  │              STORAGE LAYER                   │    │
│  │                                              │    │
│  │  ┌────────┐   ┌────────┐   ┌─────────────┐  │    │
│  │  │  S3    │   │  PVC   │   │   MLflow     │  │    │
│  │  │(durable│   │(fast   │   │  (registry,  │  │    │
│  │  │ store) │   │ local) │   │   lineage)   │  │    │
│  │  └────────┘   └────────┘   └─────────────┘  │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌──────────────┐  ┌────────────┐  ┌───────────┐   │
│  │Drift Monitor │  │Cost Tracker│  │ Approval  │   │
│  │              │  │            │  │ Service   │   │
│  └──────────────┘  └────────────┘  └───────────┘   │
└─────────────────────────────────────────────────────┘
```


## Data Flow: Fine-Tune Job

```
1. Client  ──POST /jobs──>  API Gateway
2. Gateway:  validate Pydantic schema + check quota + check idempotency
3. Gateway:  insert job row (status=SUBMITTED) into Postgres
4. Gateway:  dispatch to Temporal via Factory(job_type="fine_tune")
             => starts TrainingWorkflow on CPU_TASK_QUEUE

5. [CPU] Activity: validate_dataset
         - Check dataset version exists in S3, validate schema/format
6. [CPU] Activity: preprocess_data
         - Tokenize, dedup, filter, write processed data to S3
7. [CPU] Activity: prepare_workspace
         - Pull processed data S3 -> PVC, pull base model S3 -> PVC

8. [GPU] Activity: run_training     ← queue switch to GPU_TASK_QUEUE
         - Run fine-tuning (LoRA/QLoRA/full) on PVC
         - Heartbeat every 60s (Temporal detects stuck jobs)
         - Checkpoint every N steps -> PVC -> S3
         - On preemption: Temporal retries from last S3 checkpoint

9. [CPU] Activity: upload_artifacts
         - Push final model/adapter PVC -> S3 (checksum + idempotent)
         - Log to MLflow (metrics, params, artifact URIs)

10. [GPU] Activity: run_evaluation
         - Run offline benchmarks (MMLU, HumanEval, etc.)
         - Compare against eval_policy thresholds

11. [CPU] Activity: register_model
         - Register in MLflow with stage="dev"
         - Link lineage: model -> dataset_version + config + code

12. Status -> COMPLETED (or EVAL_FAILED if thresholds not met)
```


## Data Flow: HPO Job (Fanout + Pruning)

```
1. Gateway validates + dispatches HPOWorkflow

2. [CPU] Activity: generate_trial_configs
         - Sample from param_space (Bayesian/random/grid)
         - Generate up to max_trials configs

3. HPOWorkflow fans out: starts N child TrainingWorkflows
         - Each child = one trial (independent Temporal workflow)
         - Each child runs on GPU_TASK_QUEUE

4. HPO controller (parent workflow):
         - Polls child metrics periodically
         - Prunes bottom performers (median/percentile strategy)
         - Sends cancel signal to pruned children
         - Children checkpoint before terminating

5. [CPU] Activity: select_best_trial
         - Compare all completed trials on objective_metric
         - Register best model in MLflow

6. [GPU] Activity: evaluate_best
         - Full eval suite on the winning model

7. Register + optional promote
```

WHY child workflows: Each trial is independently retryable and cancellable.
WHY pruning in parent: Saves 30–50% GPU hours on bad trials.


## Data Flow: Retraining (Trigger -> Train -> Eval -> Canary -> Promote)

```
1. Drift Monitor detects performance degradation or data drift
         - Emits retrain signal (via event bus or Temporal signal)

2. RetrainingWorkflow starts:
         a. Storm check: was there a retrain in the last N hours? If yes, skip.
            WHY: Prevents retrain storms from noisy drift signals.
         b. Assemble latest data (incremental or full)

3. Runs TrainingWorkflow as child (same fine-tune flow above)

4. [GPU] Activity: run_evaluation
         - Compare new model vs current production model
         - Must beat current model on key metrics

5. [CPU] Activity: request_approval (if auto_promote=false)
         - Create approval ticket, wait for human sign-off

6. [CPU] Activity: canary_rollout
         - Deploy new model to canary (e.g., 10% traffic)
         - Monitor for N hours

7. [CPU] Activity: promote_or_rollback
         - If canary passes: full promotion in MLflow (staging -> prod)
         - If canary fails: rollback, alert, mark job as ROLLBACK

8. Update lineage + close the loop
```


## Data Flow: RLHF Pipeline

```
1. Gateway validates RLHFWorkflow submission
         - Validates preference dataset ref + safety config

2. [CPU] Activity: validate_preference_data
         - Check format (chosen/rejected pairs), dedup, version

3. [GPU] Activity: train_reward_model
         - Train reward model on preference data
         - Checkpoint + log to MLflow

4. [GPU] Activity: run_alignment_training
         - If method=PPO: use reward model to score generations, optimize policy
         - If method=DPO: direct preference optimization (no separate reward model)
         - Checkpoint regularly (long-running)

5. [GPU] Activity: run_safety_evaluation
         - Run safety benchmarks (ToxiGen, bias, etc.)
         - Compare against safety_thresholds
         - HARD GATE: fail if any threshold violated

6. [GPU] Activity: run_quality_evaluation
         - Standard quality benchmarks

7. [CPU] Activity: register_aligned_model
         - Register in MLflow with full lineage
         - Includes: base model + preference data version + reward model ref

8. Approval + canary (same as retraining flow)
```

WHY safety is a HARD GATE: Alignment failures are reputational/legal risks.


## Temporal Architecture

### Workflows

| Workflow | Trigger | Key Activities |
|---|---|---|
| `TrainingWorkflow` | Job submit (fine_tune) | validate, preprocess, train, upload, eval, register |
| `HPOWorkflow` | Job submit (hpo) | generate configs, fan out children, prune, select best |
| `RetrainingWorkflow` | Drift signal / schedule | storm check, assemble data, child train, eval, canary, promote |
| `RLHFWorkflow` | Job submit (rlhf) | validate prefs, reward model, alignment, safety eval, register |
| `EvaluationWorkflow` | Job submit (eval_only) | run benchmarks, compare, report |

### Task Queues

| Queue | Workers | Activities | WHY |
|---|---|---|---|
| `CPU_TASK_QUEUE` | CPU pool | validate, preprocess, tokenize, upload, register, package | Cheap work on cheap nodes |
| `GPU_TASK_QUEUE` | GPU pool | train, eval, reward model, PPO/DPO | Expensive work on GPU nodes |

### Temporal Factory (routing)

```python
# Pseudocode — Factory routes job_type to workflow config
WORKFLOW_REGISTRY = {
    "fine_tune": {
        "workflow": TrainingWorkflow,
        "default_queue": "CPU_TASK_QUEUE",  # starts on CPU
        "retry_policy": RetryPolicy(max_attempts=3, backoff=2.0),
        "timeout": timedelta(hours=48),
    },
    "hpo": {
        "workflow": HPOWorkflow,
        "default_queue": "CPU_TASK_QUEUE",
        "retry_policy": RetryPolicy(max_attempts=2, backoff=2.0),
        "timeout": timedelta(hours=72),
    },
    "rlhf": {
        "workflow": RLHFWorkflow,
        "default_queue": "CPU_TASK_QUEUE",
        "retry_policy": RetryPolicy(max_attempts=2, backoff=2.0),
        "timeout": timedelta(hours=96),
    },
    "retrain": {
        "workflow": RetrainingWorkflow,
        "default_queue": "CPU_TASK_QUEUE",
        "retry_policy": RetryPolicy(max_attempts=3, backoff=2.0),
        "timeout": timedelta(hours=72),
    },
    "eval_only": {
        "workflow": EvaluationWorkflow,
        "default_queue": "GPU_TASK_QUEUE",
        "retry_policy": RetryPolicy(max_attempts=3, backoff=1.5),
        "timeout": timedelta(hours=4),
    },
}

def dispatch_job(job_spec: JobSpec) -> str:
    config = WORKFLOW_REGISTRY[job_spec.job_type]
    workflow_id = f"wf-{job_spec.job_type}-{job_spec.idempotency_key}"
    return temporal_client.start_workflow(
        config["workflow"].run,
        job_spec,
        id=workflow_id,                        # idempotent start
        task_queue=config["default_queue"],
        retry_policy=config["retry_policy"],
        execution_timeout=config["timeout"],
    )
```

WHY Factory: Single dispatch point; adding a new job type = one registry entry.
WHY workflow_id includes idempotency_key: Temporal deduplicates by workflow ID.


### Activity Queue Switching

```python
# Inside TrainingWorkflow — switch from CPU to GPU queue mid-workflow
async def run(self, spec: JobSpec):
    # CPU activities (cheap)
    await workflow.execute_activity(
        validate_dataset, spec.data_refs,
        task_queue="CPU_TASK_QUEUE",
        start_to_close_timeout=timedelta(minutes=30),
    )
    await workflow.execute_activity(
        preprocess_data, spec.data_refs,
        task_queue="CPU_TASK_QUEUE",
        start_to_close_timeout=timedelta(hours=2),
    )

    # GPU activities (expensive) — queue switch
    await workflow.execute_activity(
        run_training, spec,
        task_queue="GPU_TASK_QUEUE",
        start_to_close_timeout=timedelta(hours=24),
        heartbeat_timeout=timedelta(minutes=5),  # detect stuck GPU jobs
    )
```

WHY heartbeat on GPU: GPU jobs are expensive. Detect stuck/crashed jobs within 5 min.


## Storage Architecture

### Lifecycle: S3 -> PVC -> Run -> PVC -> S3

```
┌─────────┐     pull      ┌─────────┐    run     ┌─────────┐
│   S3    │ ──────────> │   PVC   │ ────────> │  Train  │
│ (durable│             │ (fast   │           │  on GPU │
│  source)│             │  local) │           │         │
└─────────┘             └─────────┘           └────┬────┘
     ▲                       ▲                     │
     │      push (final)     │    checkpoint       │
     └───────────────────────┴─────────────────────┘
```

- **Start**: Pull dataset + base model from S3 to PVC
  - WHY: PVC (NVMe) is 10–100x faster than S3 for random reads during training
- **During training**: Checkpoint to PVC, then async copy PVC -> S3
  - WHY: Checkpoint must survive pod eviction
- **End**: Final model/adapter PVC -> S3, then register in MLflow
  - WHY: S3 is durable; PVC is ephemeral

### Consistency guarantees

- **Checksums** on every S3 upload (SHA256)
- **Idempotent uploads** (same key + checksum = skip)
- **Manifest file** per job listing all artifacts + checksums
- **Compensation**: if S3 upload fails, retry; if MLflow register fails, retry from S3 artifacts

### MLflow Registry

- Stages: `dev` -> `staging` -> `prod` -> `archived`
- Every model version links to: run_id, dataset_version, config_hash, code_commit
- Rollback = promote previous version back to `prod`

WHY MLflow: Industry standard; handles versioning, staging, metrics, lineage.


## Fairness & Quotas (where they apply)

| Layer | Enforcement |
|---|---|
| API submission | Reject if project budget exhausted (GPU-hours) |
| Job Scheduler | Weighted fair queue — priority based on project tier + budget remaining |
| Temporal dispatch | Project-level concurrency limits (max N workflows) |
| K8s scheduling | ResourceQuotas per namespace (CPU, GPU, memory limits) |
| Runtime | Pause job if budget exceeded mid-run (after checkpoint) |

WHY at every layer: One enforcement point is not enough. Budget check at submit doesn't prevent runtime overrun.


## TL;DR (Interview Summary)

- FastAPI gateway + Pydantic validation -> Job Scheduler -> Temporal dispatch
- Temporal Factory routes job_type to workflow + queue + retry profile
- CPU_TASK_QUEUE for cheap work; GPU_TASK_QUEUE for training — never waste GPUs
- 5 workflows: Training, HPO (fanout children), Retraining (trigger-based), RLHF (multi-stage), Eval
- Storage: S3 -> PVC (fast) -> train -> PVC -> S3 (durable) -> MLflow (registry)
- HPO uses child workflows + parent-driven pruning to control costs
- RLHF has hard safety gate — blocks promotion if thresholds violated
- Fairness enforced at 5 layers: API, scheduler, Temporal, K8s, runtime
