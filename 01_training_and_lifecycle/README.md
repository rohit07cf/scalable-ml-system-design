# Training and Lifecycle

## What This Section Covers

- Fine-tuning LLMs with parameter-efficient methods (LoRA, QLoRA)
- Hyperparameter tuning and experiment tracking at scale
- Continuous retraining pipelines with drift detection
- RLHF and alignment training workflows


## What Interviewers Usually Test

- Can you design a training pipeline that handles data, compute, and versioning end-to-end?
- Do you understand the trade-offs between full fine-tuning, adapter methods, and prompt tuning?
- Can you explain how to keep models fresh without breaking production?


## Suggested Study Order

1. `design_finetuning_llamafactory` -- start here, covers core fine-tuning concepts
2. `design_hparam_tuning_mlflow` -- experiment tracking and search strategies
3. `design_continuous_retraining` -- drift detection, automated pipelines
4. `design_multi_tenant_training` -- isolation, scheduling, resource sharing
5. `design_rlhf_pipeline` -- reward modeling, PPO/DPO, human feedback loops


## Fast Revision Path

- Skim "Must explain in interview" in each subfolder (5 min total)
- Review the HLD for fine-tuning and continuous retraining (5 min)
- Rehearse one end-to-end walkthrough aloud: data in, model out, deployed (5 min)
