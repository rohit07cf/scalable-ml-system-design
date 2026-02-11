# Design: Hyperparameter Tuning with Experiment Tracking (MLflow)

Design a scalable hyperparameter optimization system integrated with experiment tracking for ML and LLM training jobs.


## Key Requirements

- Support grid, random, Bayesian (Optuna), and early-stopping strategies across distributed workers
- Track every trial's params, metrics, artifacts, and environment in a centralized experiment store
- Integrate with existing training pipelines (PyTorch, HuggingFace) with minimal code changes


## Core Components

- Search controller -- generates trial configs, applies pruning, manages the search budget
- Trial runner -- executes a single training run with injected hyperparams, reports metrics back
- Experiment store -- MLflow tracking server with params, metrics, tags, and artifact logging
- Model registry -- promotes best trial to staging/production with approval workflow
- Scheduler -- allocates GPU/CPU resources across concurrent trials, supports spot instances


## Key Trade-Offs

- Bayesian search vs random: better sample efficiency but adds coordination overhead and sequential bottleneck
- Per-trial checkpointing vs final-only: enables early stopping but increases storage cost 3-5x
- Shared cluster vs dedicated trial VMs: cost-efficient but introduces noisy-neighbor GPU contention


## Must Explain in Interview

- Why random search often beats grid search: higher effective coverage in high-dimensional spaces
- How Bayesian optimization works: surrogate model (GP/TPE), acquisition function, explore-exploit
- Early stopping with Successive Halving / Hyperband: allocate budget to promising trials, prune losers
- MLflow's tracking hierarchy: experiment > run > params + metrics + artifacts + tags
- How to handle LLM-specific hyperparams: learning rate warmup, LoRA rank, gradient accumulation steps
