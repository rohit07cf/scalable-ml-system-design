# 7. Wrap Up


## Bottlenecks

| Bottleneck | Why It Hurts | Mitigation |
|---|---|---|
| **GPU pool exhaustion** | All teams blocked; HPO can monopolize | Fair quotas, HPO pruning, spot instances, priority preemption |
| **S3 throughput during checkpoint storms** | Many jobs checkpointing simultaneously | Stagger checkpoint intervals, async uploads, PVC as buffer |
| **Temporal task queue backlog** | Jobs pile up if workers can't keep pace | Autoscale workers, per-project concurrency limits, backpressure |
| **MLflow write contention** | Many jobs logging metrics + registering simultaneously | Batch metric writes, retry with backoff, async registration |
| **PVC provisioning latency** | New pods wait for storage attach | Pre-provisioned PVC pool, reuse across runs in same project |
| **Large model downloads** | 70B model = ~140 GB to pull from S3 per job | Model cache on GPU nodes (shared read-only PVC), content-addressed dedup |


## Scaling Strategies

### GPU Scaling
- **Cluster autoscaler**: Scale GPU node pool based on pending pods
- **Spot + on-demand mix**: 70% spot for HPO/eval, on-demand for critical training
- **Priority preemption**: Low-priority HPO trials preempted for high-priority fine-tune
- WHY mix: Spot saves ~60–70% cost; on-demand guarantees SLA for critical jobs

### CPU Scaling
- **HPA on CPU workers**: Scale based on CPU_TASK_QUEUE depth
- CPU is cheap; over-provision slightly to avoid blocking GPU pipeline
- WHY: A CPU bottleneck delays GPU start = wasted GPU idle time

### Temporal Scaling
- **Multi-node Temporal cluster** with separate history, matching, frontend services
- Scale matching service independently (it handles task dispatch)
- WHY: Temporal is not the bottleneck at our scale (~500 wf/day), but HA is critical

### Storage Scaling
- **S3**: Scales automatically (no action needed)
- **PVC**: Pre-provisioned pool per GPU node; reclaim after job ends
- **MLflow**: Scale backend DB (Postgres) read replicas for query load
- WHY: Storage is rarely the bottleneck, but PVC provisioning latency can delay job start


## Trade-offs + Alternatives

### Orchestration: Temporal vs Alternatives

| Option | Pros | Cons | When to Choose |
|---|---|---|---|
| **Temporal** (chosen) | Durable state, retries, heartbeats, child workflows, visibility | Operational overhead, learning curve | Complex multi-step workflows with failure recovery |
| Airflow | Familiar, large ecosystem | DAG-based (rigid), poor real-time, no heartbeats | Simple batch ETL; not for interactive job control |
| Argo Workflows | K8s-native, DAG execution | No durable state across restarts, weaker retry semantics | Short K8s-native pipelines |
| Custom queue (Redis/SQS) | Simple, low overhead | Must build retry/state/visibility from scratch | Very simple job dispatch only |

WHY Temporal: Durable workflows + heartbeats + child workflow fanout + signal handling is exactly what training orchestration needs.

### Storage: PVC + S3 vs Alternatives

| Option | Pros | Cons | When to Choose |
|---|---|---|---|
| **PVC + S3** (chosen) | Fast local I/O + durable remote store | Sync complexity, data movement | Training jobs with heavy I/O |
| S3 only (FUSE mount) | Simple, no sync needed | 10–100x slower random reads, FUSE overhead | Small models, light I/O |
| Shared NFS / EFS | Simple sharing, no sync | Performance at scale, single point of failure | Small teams, light workloads |
| Ceph / MinIO | Self-hosted, flexible | Operational overhead | On-prem with no cloud storage |

WHY PVC + S3: Training I/O is random-read heavy (data loading). PVC (NVMe) is 10–100x faster than FUSE-mounted S3.

### HPO: Bayesian vs Grid vs Random

| Option | Pros | Cons | When to Choose |
|---|---|---|---|
| **Bayesian (Optuna)** (default) | Sample-efficient, works with pruning | More complex, sequential dependence | Default for most HPO jobs |
| Random | Simple, parallelizable, surprisingly effective | Less sample-efficient | Large param spaces, many GPUs available |
| Grid | Exhaustive, reproducible | Combinatorial explosion | Small param spaces only (2–3 params, few values) |

WHY Bayesian default: Best cost/quality ratio. Pruning + Bayesian = ~50–70% GPU savings vs grid.

### Model Registry: MLflow vs Alternatives

| Option | Pros | Cons | When to Choose |
|---|---|---|---|
| **MLflow** (chosen) | Industry standard, staging, versioning, lineage | UI is basic, scaling needs tuning | Enterprise ML platforms |
| Weights & Biases | Better UI, collaboration | SaaS cost, vendor lock-in | If UI/collaboration is top priority |
| Custom DB | Full control | Must build everything | Unique requirements not met by existing tools |

WHY MLflow: Open source, self-hosted, staged promotion, industry standard. Avoid vendor lock-in.

### RLHF: PPO vs DPO

| Option | Pros | Cons | When to Choose |
|---|---|---|---|
| PPO | Flexible, any reward signal | Complex (4 models), unstable, expensive | Complex multi-objective alignment |
| **DPO** (default recommendation) | Simple, stable, cheaper (2 models) | Tied to preference data quality | Clean preference data, standard alignment |

WHY DPO as default: 2–3x cheaper, simpler pipeline, more stable. PPO when reward signal is complex.


## Final "8-Minute Interview Close" Bullets

> Use these to close your interview answer cleanly.

1. **One API, five job types** — Pydantic-validated JobSpec with idempotency key handles fine-tune, HPO, retrain, RLHF, and eval-only through a single `POST /jobs` endpoint.

2. **Temporal orchestrates everything** — Durable workflows with Factory-routed dispatch, CPU/GPU queue separation, heartbeats on GPU activities, child workflow fanout for HPO.

3. **Kubernetes runs the compute** — CPU worker pool for cheap prep work, GPU worker pool with taints/tolerations, namespace isolation per project, cluster autoscaler for elasticity.

4. **Storage lifecycle: S3 -> PVC -> train -> S3 -> MLflow** — PVC for fast training I/O, S3 for durability, MLflow for registry + lineage. Checksums + manifests ensure consistency.

5. **Cost governance at every layer** — GPU-hour budgets per project, HPO pruning (saves 30–50%), spot policies, fair scheduling with weighted priorities, runtime budget enforcement.

6. **Failure-resilient by design** — Checkpoint-based resume for preemption, two-layer idempotency, Temporal retries with backoff, compensation steps for partial failures.

7. **Eval + safety gates before promotion** — No model reaches staging/prod without passing benchmarks + safety checks + optional human approval.

8. **Closed-loop retraining** — Drift/perf monitoring triggers retrain; storm prevention via cooldown + cap + dedup; canary rollout before promotion.


## TL;DR (Interview Summary)

- GPU pool is the primary bottleneck — solve with fair quotas, HPO pruning, spot mix, autoscaler
- Temporal chosen over Airflow/Argo for durable state + heartbeats + child workflows
- PVC + S3 chosen over FUSE for 10–100x I/O performance during training
- Bayesian HPO + pruning is default — saves 50–70% GPU cost vs grid
- DPO is default alignment method — 2–3x cheaper than PPO, simpler pipeline
- MLflow is registry of choice — open source, staged promotion, lineage
- Close the interview with: one API, Temporal, K8s, storage lifecycle, cost governance, failure resilience, eval gates, closed-loop retraining
