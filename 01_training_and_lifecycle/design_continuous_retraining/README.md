# Design: Continuous Retraining Pipeline

Design an automated pipeline that detects model staleness, triggers retraining on fresh data, validates the new model, and promotes it to production without downtime.


## Key Requirements

- Detect data drift and performance degradation using statistical tests and live metric monitoring
- Retrain on incremental or full datasets on a schedule or trigger, with full lineage tracking
- Deploy new models through a validation gate (shadow mode, canary, A/B) before full rollout


## Core Components

- Drift detector -- monitors feature distributions and prediction quality; fires retrain signals
- Data assembler -- builds training sets from new + historical data, applies dedup and quality filters
- Training orchestrator -- kicks off training jobs (Airflow / Kubeflow), tracks lineage from data to model
- Validation gate -- runs offline evals, shadow scoring, and canary checks before promotion
- Model swapper -- blue-green or rolling deployment of the new model with instant rollback


## Key Trade-Offs

- Scheduled retrain vs drift-triggered: predictable cost vs faster adaptation; most teams start with scheduled
- Full retrain vs incremental update: simpler validation vs lower compute; incremental risks catastrophic forgetting
- Tight validation gates vs fast rollout: safety vs freshness; stale models also have cost


## Must Explain in Interview

- How to detect drift: PSI / KL-divergence on features, performance decay on golden test sets
- Data versioning: why every retrain must pin an immutable dataset snapshot (DVC, Delta Lake, or artifact store)
- The feedback loop: production predictions generate labels that feed back into the next training cycle
- Rollback strategy: keep the previous model hot, route traffic back in under 60 seconds on metric drop
- Why lineage matters: for debugging regressions you need data version + code version + config version
