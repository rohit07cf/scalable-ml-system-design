# 6. Deep Dives


## 6.1 Job State Machine

```
                          ┌──────────┐
                          │SUBMITTED │
                          └────┬─────┘
                   quota OK    │    quota fail
                  ┌────────────┤────────────┐
                  ▼            │            ▼
             ┌────────┐       │      ┌──────────┐
             │ QUEUED │       │      │ REJECTED │
             └───┬────┘       │      └──────────┘
     scheduler   │            │
     picks it    │            │
                 ▼            │
             ┌────────┐      │
        ┌───>│RUNNING │<─────┘ (retry from checkpoint)
        │    └──┬──┬──┘
        │       │  │
        │       │  ├── user cancel ──> CANCELLED
        │       │  ├── user pause ──> PAUSED ──resume──> RUNNING
        │       │  ├── budget exceeded ──> PAUSED (auto)
        │       │  │
        │       │  └── preemption/crash
        │       │         │
        │       │         ▼
        │       │     checkpoint saved?
        │       │      yes/     \no
        │       │       │        │
        │       ▼       ▼        ▼
        │    training  QUEUED   FAILED
        │    done?    (retry)
        │     │
        │     ▼
        │  ┌───────────┐
        │  │EVALUATING │
        │  └──┬────────┘
        │     │
        │     ├── eval passes ──> COMPLETED
        │     └── eval fails  ──> EVAL_FAILED
        │
        └──── (retry from checkpoint after preemption)
```

### Transitions

| From | To | Trigger |
|---|---|---|
| SUBMITTED | QUEUED | Quota check passes |
| SUBMITTED | REJECTED | Quota check fails |
| QUEUED | RUNNING | Scheduler dispatches |
| RUNNING | PAUSED | User pause OR budget exceeded |
| PAUSED | RUNNING | User resume (if budget restored) |
| RUNNING | CANCELLED | User cancel |
| RUNNING | QUEUED | Preemption with checkpoint (retry) |
| RUNNING | FAILED | Crash without checkpoint / max retries |
| RUNNING | EVALUATING | Training completes |
| EVALUATING | COMPLETED | Eval passes thresholds |
| EVALUATING | EVAL_FAILED | Eval fails thresholds |

WHY explicit EVAL_FAILED: Distinguishes "training worked but model is bad" from "infra failure."
WHY PAUSED on budget: Saves checkpoint, doesn't lose work, alerts team to add budget.


## 6.2 Idempotency Strategy

### Problem
Network retries can cause the same job submission to hit the API multiple times.

### Solution

1. Client generates `idempotency_key` (e.g., `"ft-chatbot-v2-2024-run-3"`)
2. API does: `INSERT INTO jobs ... ON CONFLICT (idempotency_key) DO NOTHING`
3. If conflict: return 409 with existing `job_id`
4. Temporal workflow ID = `f"wf-{job_type}-{idempotency_key}"`
   - Temporal's `start_workflow` with same ID is a no-op if already running

```python
# Pseudocode
async def submit_job(spec: JobSpec):
    # DB-level dedupe
    existing = await db.get_job_by_idempotency_key(spec.idempotency_key)
    if existing:
        return Response(status=409, body={"job_id": existing.id})

    job = await db.insert_job(spec)  # UNIQUE constraint is the safety net

    # Temporal-level dedupe (workflow ID collision = no-op)
    wf_id = f"wf-{spec.job_type}-{spec.idempotency_key}"
    await temporal_client.start_workflow(..., id=wf_id)

    return Response(status=201, body={"job_id": job.id})
```

WHY two layers: DB catches API retries; Temporal catches scheduler retries.


## 6.3 Retry / Timeout / Heartbeat Profiles

### CPU Activities

| Setting | Value | WHY |
|---|---|---|
| `start_to_close_timeout` | 30 min (validate) / 2h (preprocess) | CPU tasks are bounded; fail fast if stuck |
| `retry_max_attempts` | 5 | CPU tasks are cheap to retry |
| `retry_backoff` | 1s initial, 2x multiplier | Quick retries for transient errors |
| `heartbeat_timeout` | None | Short tasks don't need heartbeat |

### GPU Activities

| Setting | Value | WHY |
|---|---|---|
| `start_to_close_timeout` | 24–72h | Training can be long (especially full FT, RLHF) |
| `retry_max_attempts` | 3 | Each retry resumes from checkpoint (not from scratch) |
| `retry_backoff` | 30s initial, 2x multiplier | Wait for GPU reallocation |
| `heartbeat_timeout` | 5 min | Detect dead/stuck GPU pods quickly; GPUs are expensive |

### Heartbeat Pattern (GPU training)

```python
# Inside GPU training activity
async def run_training(spec: JobSpec):
    model, step = load_from_checkpoint(spec)  # resume if checkpoint exists
    for batch in dataloader(start_from=step):
        loss = train_step(model, batch)
        step += 1

        if step % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(model, step)       # PVC -> S3

        # Heartbeat tells Temporal "I'm alive" + reports progress
        activity.heartbeat({"step": step, "loss": loss})
```

WHY heartbeat every step: If GPU pod dies, Temporal detects within `heartbeat_timeout` and retries.
WHY checkpoint + heartbeat together: Heartbeat proves liveness; checkpoint enables resume.


## 6.4 Checkpointing + Resume for Preemption

### Problem
Spot instances can be reclaimed with 30s–2min warning. Multi-hour training progress must not be lost.

### Strategy

1. **Periodic checkpoints** (every N steps or M minutes) saved to PVC
2. **Async S3 upload**: Background thread copies PVC checkpoint -> S3
3. **On preemption signal (SIGTERM)**:
   - Save emergency checkpoint to PVC
   - Upload to S3 (best-effort within grace period)
   - Exit cleanly
4. **On retry**:
   - Temporal retries the activity
   - Activity checks S3 for latest checkpoint
   - Loads model + optimizer state + step counter
   - Resumes dataloader from correct position

```python
# Resume logic
def load_from_checkpoint(spec):
    checkpoint_uri = get_latest_checkpoint(spec.job_id)  # from S3
    if checkpoint_uri:
        state = download_checkpoint(checkpoint_uri)
        return state["model"], state["step"]
    else:
        return load_base_model(spec.model_ref), 0
```

### Failure: Partial checkpoint upload

- S3 uploads use multipart with checksum verification
- On resume: validate checkpoint checksum before loading
- If corrupt: fall back to previous valid checkpoint
- WHY: Corrupt checkpoint = worse than no checkpoint

### Failure: No checkpoint saved (immediate crash)

- Retry from step 0 (or last valid checkpoint)
- Temporal `retry_max_attempts` limits total retries
- After max retries: mark job FAILED, alert team


## 6.5 HPO Pruning / Early Stopping

### Problem
HPO can spawn 50–100 trials. Running all to completion wastes GPU hours on bad configs.

### Strategy: Median Pruning (Optuna-style)

1. After each trial completes `min_steps_before_prune` steps:
   - Report intermediate metric to parent HPOWorkflow
2. Parent compares trial's metric to median of all trials at same step
3. If below median: send cancel signal to child workflow
4. Child receives signal, saves checkpoint, terminates

### Implementation in Temporal

```python
# HPOWorkflow (parent)
async def run(self, spec: JobSpec):
    trial_configs = generate_trials(spec.hpo_config)
    children = []

    for config in trial_configs:
        child = await workflow.start_child_workflow(
            TrainingWorkflow.run,
            config,
            id=f"trial-{spec.idempotency_key}-{config.trial_id}",
        )
        children.append(child)

    # Pruning loop
    while active_children(children):
        await workflow.sleep(timedelta(minutes=5))  # poll interval
        metrics = collect_child_metrics(children)
        to_prune = median_prune(metrics, spec.hpo_config.pruning)
        for child in to_prune:
            await child.signal("cancel")  # graceful cancel
```

WHY median pruning: Simple, effective, well-understood. Saves 30–50% GPU hours.
WHY signal (not terminate): Child gets chance to save checkpoint.


## 6.6 RLHF Pipeline: PPO vs DPO

### PPO (Proximal Policy Optimization)
- **Pipeline**: Preference data -> train reward model -> generate responses -> score with RM -> optimize policy via PPO
- **Pros**: More flexible, works with any reward signal
- **Cons**: 4 models in memory (policy, ref, RM, value), unstable training, higher GPU cost
- **When**: Complex reward signals, multi-objective alignment

### DPO (Direct Preference Optimization)
- **Pipeline**: Preference data -> directly optimize policy using preference pairs (no RM needed)
- **Pros**: Simpler, fewer models, more stable, lower GPU cost
- **Cons**: Less flexible, tied to preference data quality
- **When**: Clean preference data, simpler alignment goals, cost-sensitive

### Platform design impact

| Concern | PPO | DPO |
|---|---|---|
| GPU activities | 2 separate (RM train + PPO) | 1 (DPO train) |
| Memory per GPU | ~4x model size | ~2x model size |
| Checkpoint complexity | Must checkpoint RM + policy | Just policy |
| Typical GPU-hours (7B) | 12–20h | 4–8h |

WHY support both: Different teams have different needs. Strategy pattern makes this a config choice.

```python
# Strategy pattern
ALIGNMENT_STRATEGIES = {
    "ppo": PPOAlignmentStrategy,
    "dpo": DPOAlignmentStrategy,
}
strategy = ALIGNMENT_STRATEGIES[spec.rlhf_config.alignment_method]
strategy.train(model, data, config)
```


## 6.7 Fair Scheduling

### Problem
One team running a 100-trial HPO sweep can starve other teams' single fine-tune jobs.

### Multi-layer fairness

**Layer 1: Submission-time budget check**
- Reject if project GPU-hours budget is exhausted
- WHY: Don't queue work that can't possibly run

**Layer 2: Priority queue with weighted fair sharing**
```
effective_priority = base_priority
                   + project_tier_bonus       (platinum=+10, gold=+5)
                   - starvation_penalty       (wait_time / 60 → +1 per hour)
                   - hpo_penalty              (if HPO, -3 per running trial)
```
- WHY `hpo_penalty`: Prevents HPO from dominating the queue
- WHY `starvation_penalty`: Jobs waiting longer get priority boost

**Layer 3: Temporal concurrency limits**
- Per-project: max N concurrent workflows (e.g., 10)
- WHY: Caps blast radius of one project's burst

**Layer 4: K8s ResourceQuotas**
- Per-namespace GPU limits (e.g., max 8 GPUs per project)
- WHY: Hard ceiling even if scheduler allows more

**Layer 5: Runtime budget enforcement**
- Monitor GPU-hours consumed per running job
- Pause if budget exceeded mid-run (after checkpoint)
- WHY: Submission-time estimate may be wrong


## 6.8 Storage Consistency: PVC / S3 / MLflow

### Problem
Three storage systems must stay consistent. Partial failures leave inconsistent state.

### Consistency protocol

```
1. Train on PVC (local fast storage)
2. Checkpoint PVC -> S3  (with SHA256 checksum)
3. Final model PVC -> S3  (with checksum + manifest)
4. Register in MLflow     (point to S3 URI)
5. Clean up PVC
```

### Failure scenarios + compensation

| Failure | Impact | Compensation |
|---|---|---|
| S3 upload fails mid-checkpoint | Partial file in S3 | Retry upload; S3 multipart auto-cleans incomplete uploads |
| S3 upload succeeds, MLflow register fails | Orphan artifact in S3 | Retry register; artifact is idempotent (same key = overwrite). Background job sweeps orphans |
| PVC lost (pod eviction) before S3 upload | Checkpoint lost | Resume from last S3 checkpoint (may lose some steps) |
| MLflow down | Can't register model | Retry with backoff. If still down: save registration payload to DB, process when MLflow recovers |

### Manifest file (per job)

```json
{
  "job_id": "job-abc",
  "artifacts": [
    {"type": "checkpoint", "uri": "s3://...step-4000", "sha256": "abc123", "step": 4000},
    {"type": "checkpoint", "uri": "s3://...step-8000", "sha256": "def456", "step": 8000},
    {"type": "final_model", "uri": "s3://...final", "sha256": "ghi789"}
  ],
  "mlflow_run_id": "run-xyz"
}
```

WHY manifest: Single source of truth for all artifacts of a job. Enables verification + cleanup.


## 6.9 Retraining Triggers + Storm Prevention

### Triggers

| Trigger | Source | Example |
|---|---|---|
| Schedule | Cron (Temporal scheduled workflow) | Retrain every Monday 2am |
| Drift detected | Drift monitor (statistical test on input distribution) | KL divergence > threshold |
| Performance drop | Monitoring (accuracy/latency regression) | Accuracy drops 5% below baseline |
| Manual | API call | Operator triggers retrain |

### Storm prevention

Problem: Noisy metrics can trigger dozens of retrain requests in quick succession.

**Cooldown**:
- After a retrain starts, suppress new retrain triggers for N hours (e.g., 6h)
- Implementation: Check `last_retrain_started_at` in DB before starting

**Cap**:
- Max K retrain jobs per project per day (e.g., 3)
- Implementation: COUNT recent retrain jobs for project

**Dedup**:
- Use idempotency key = `f"retrain-{project}-{date}"` for schedule-based
- Use idempotency key = `f"retrain-{project}-{trigger_hash}"` for event-based

```python
# RetrainingWorkflow storm check
async def run(self, spec: RetrainSpec):
    last_retrain = await db.get_last_retrain(spec.project_id)
    if last_retrain and (now() - last_retrain.started_at) < COOLDOWN:
        return {"status": "skipped", "reason": "cooldown active"}

    retrain_count = await db.count_retrains_today(spec.project_id)
    if retrain_count >= MAX_DAILY_RETRAINS:
        return {"status": "skipped", "reason": "daily cap reached"}

    # Proceed with retraining...
```

WHY cooldown + cap + dedup: Three independent safeguards. Any one prevents storms.


## TL;DR (Interview Summary)

- Job state machine has 8 states; EVAL_FAILED is distinct from FAILED (model bad vs infra bad)
- Two-layer idempotency: DB UNIQUE key + Temporal workflow ID dedup
- GPU heartbeat every step (5 min timeout) — detect dead pods fast, GPUs are expensive
- Checkpoint + async S3 upload + SIGTERM handler = preemption-safe
- HPO pruning via parent workflow signaling children — saves 30–50% GPU hours
- PPO vs DPO is a Strategy pattern config choice; DPO is 2–3x cheaper
- Fair scheduling uses 5 layers: submit check, weighted queue, Temporal limits, K8s quotas, runtime budget
- Storage consistency via checksums + manifests + compensation steps + orphan cleanup
