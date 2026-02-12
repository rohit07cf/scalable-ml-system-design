# 06 — Storage and Checkpointing


## Why Storage Matters

- A single checkpoint of a 70B model = **~140 GB** (weights only, fp16)
- With optimizer state: **~560 GB** per full checkpoint
- 1T+ MoE model checkpoint: **multiple TB**
- Training runs save checkpoints every **few minutes to every few hours**
- A multi-month training run accumulates **petabytes** of checkpoints and logs
- If storage fails, you lose weeks of training progress


## Parallel File Systems

Frontier clusters use high-performance parallel file systems for active training I/O:

- **Lustre** — open-source, widely deployed at HPC and frontier AI clusters
  - Striped across many OSTs (Object Storage Targets) for throughput
  - Used by Meta, many national labs

- **WEKA** — commercial parallel file system, increasingly adopted
  - Flash-native, high random I/O performance
  - Used by xAI (Colossus), several cloud-based clusters

- **GPFS / IBM Storage Scale** — IBM's parallel file system
  - Enterprise-grade, used in some HPC environments

- **DAOS** — Intel's Distributed Asynchronous Object Storage
  - Emerging option for high-performance checkpointing

### Key requirements for training storage

- **Throughput**: TB/s aggregate read/write (thousands of GPUs reading/writing simultaneously)
- **Latency**: low-latency metadata operations (many small files during logging)
- **Capacity**: petabyte-scale for checkpoints, datasets, logs
- **Reliability**: redundancy, snapshots, no single point of failure


## Object Storage (Durable / Cold)

For long-term durability, checkpoints and datasets are replicated to object storage:

- **AWS S3** — used by Anthropic (AWS partnership)
- **Google Cloud Storage (GCS)** — used by Google DeepMind
- **Azure Blob Storage** — used by OpenAI (Azure partnership)
- **On-prem object stores** (MinIO, Ceph) — used by Meta, xAI for on-prem clusters

### Pattern: Parallel FS for hot I/O, object storage for durability

```
Training GPUs
    ↕ (fast, TB/s)
Parallel file system (Lustre / WEKA)
    ↕ (async copy)
Object storage (S3 / GCS / Azure Blob)
    ↕ (replicate)
Multi-region backup
```

- Active training reads/writes hit the parallel file system
- Background processes copy checkpoints to object storage
- Critical checkpoints are replicated to a second region


## Multi-Region Redundancy

- A catastrophic failure (fire, power loss, hardware cascade) can destroy a cluster
- Critical checkpoints must survive datacenter-level failures
- **Multi-region replication**: at least one copy in a geographically separate location
- Adds latency to the replication path, but protects against total loss
- Some labs maintain "golden" checkpoints replicated to 3+ locations


## Checkpoint Details

### What's in a checkpoint

- **Model weights** (fp16/bf16): the trained parameters
- **Optimizer state**: momentum, variance (Adam) — often 2–3x weight size
- **Learning rate scheduler state**: current step, schedule parameters
- **Data loader state**: exact position in the dataset (for deterministic resume)
- **RNG states**: random seeds for reproducibility
- **Training metadata**: step count, loss curves, config

### Checkpoint sizes (realistic)

| Model | Weights Only | Full Checkpoint (w/ optimizer) |
|---|---|---|
| 7B | ~14 GB | ~56 GB |
| 70B | ~140 GB | ~560 GB |
| 200B | ~400 GB | ~1.6 TB |
| 1T MoE | ~2 TB | ~8 TB |

### Snapshot frequency

- **Periodic checkpoints**: every 5–30 minutes of training time
  - More frequent = less progress lost on failure, but more storage cost
  - Typical for frontier runs: every ~10–20 minutes

- **Milestone checkpoints**: at specific training steps (e.g., every 1000 steps)
  - Kept longer for evaluation, rollback, ablation studies

- **Best-effort emergency checkpoints**: on failure signal (SIGTERM)
  - Save what you can in the grace period before shutdown

### Storage cost

- 70B model, checkpoint every 15 min, 3-month run:
  - ~560 GB × 4 per hour × 24 hours × 90 days = **~4.8 PB** (before cleanup)
  - With retention policy (keep last N + milestones): ~100–500 TB active


## Deletion Challenges

Checkpoint management is a real operational concern:

- **Retention policies**: keep last N checkpoints + milestone checkpoints, delete the rest
  - Automated cleanup prevents petabyte-scale storage bloat

- **Legal / compliance holds**: some checkpoints cannot be deleted
  - Model lineage requirements, audit trails, regulatory holds
  - Must tag and protect "golden" checkpoints

- **Backup copies**: object storage copies may outlive the primary
  - Need coordinated deletion across parallel FS + object store + replicas

- **Accidental deletion risk**: a single bad cleanup script can destroy a training run
  - Write-protection, immutable snapshots, and deletion delays are standard safety measures

- **Verification before deletion**: checksums confirm the backup is valid
  before deleting the primary


## TL;DR (Interview Summary)

- Parallel file systems (Lustre, WEKA) for high-throughput training I/O (TB/s)
- Object storage (S3/GCS/Azure) for durable, long-term checkpoint storage
- Multi-region replication protects against datacenter-level failures
- Full checkpoint = weights + optimizer + scheduler + data position + RNG state
- 70B full checkpoint: ~560 GB; 1T MoE: ~8 TB
- Checkpoints saved every 10–20 minutes during frontier training runs
- Retention policies prevent petabyte-scale storage bloat (keep last N + milestones)
- Deletion is hard: compliance holds, multi-system coordination, accidental deletion risk
