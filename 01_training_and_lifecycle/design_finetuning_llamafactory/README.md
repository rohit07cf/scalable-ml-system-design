# Design: Fine-Tuning Platform (LLaMA-Factory Style)

Design a self-service platform that lets ML teams fine-tune open-source LLMs on custom datasets using parameter-efficient methods.


## Key Requirements

- Support LoRA, QLoRA, and full fine-tuning across multiple base models (LLaMA, Mistral, Gemma)
- Handle datasets from 1K to 10M examples with validation, versioning, and format conversion
- Provide experiment tracking, checkpoint management, and one-click deployment to inference


## Core Components

- Job orchestrator -- queues training jobs, manages GPU allocation, handles preemption
- Data pipeline -- validates, tokenizes, and shards datasets; supports chat, instruction, and completion formats
- Training engine -- wraps HuggingFace Trainer / DeepSpeed with LoRA config injection
- Artifact store -- versions checkpoints, adapters, configs, and eval results (e.g., MLflow, W&B)
- Eval harness -- runs benchmark suites (MMLU, human-eval, domain-specific) before promotion


## Key Trade-Offs

- LoRA vs full fine-tune: 10x cheaper but may underperform on narrow domains with enough data
- Single-GPU QLoRA vs multi-GPU FSDP: cost vs throughput; QLoRA fits most 7B-13B use cases
- Centralized adapter registry vs per-team storage: governance vs autonomy


## Must Explain in Interview

- How LoRA works: low-rank weight deltas, rank selection, which layers to adapt
- Why QLoRA matters: 4-bit quantization + paged optimizers enable 65B fine-tuning on a single A100
- Data quality gating: dedup, length filtering, toxicity screening before training starts
- Checkpoint strategy: save every N steps, evaluate on held-out set, promote best by eval metric
- How to serve the adapter: merge into base weights vs runtime adapter loading (latency vs flexibility)
