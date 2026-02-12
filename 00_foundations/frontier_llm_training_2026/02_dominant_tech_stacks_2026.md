# 02 — Dominant Tech Stacks (Early 2026)


## Landscape at a Glance

Two framework ecosystems dominate frontier training:

- **PyTorch + Megatron-Core / DeepSpeed** — used by most labs
- **JAX + custom infra** — used by Google DeepMind and xAI

Everything runs on either **NVIDIA GPUs** or **Google TPUs**.


## Company-by-Company Breakdown

### xAI (Grok Series)

| Aspect | Details |
|---|---|
| **Framework** | Custom JAX + Rust infrastructure |
| **Parallelism** | DP + TP + PP, MoE routing |
| **Orchestration** | Kubernetes-based cluster management |
| **Hardware** | NVIDIA H100 / H200 clusters (Colossus datacenter) |
| **Architecture** | MoE with RL-based training at scale |
| **Notable** | Built Colossus (100K+ H100s) in months; heavy Rust for performance-critical paths |

- Custom JAX stack rather than off-the-shelf Megatron
- Kubernetes for job orchestration across massive GPU pools
- MoE architecture with reinforcement learning integration
- Rapid infrastructure buildout — prioritized speed of deployment


### Meta (Llama 4 Family)

| Aspect | Details |
|---|---|
| **Framework** | PyTorch (native, Meta-developed) |
| **Parallelism** | Megatron-Core + FSDP + ZeRO |
| **Orchestration** | Internal scheduling (custom) |
| **Hardware** | NVIDIA H100 / H200 clusters (Grand Teton platform) |
| **Architecture** | Dense + MoE variants (e.g., 128 experts, 16 active) |
| **Notable** | Open-weight releases; massive cluster (600K+ GPUs reported in fleet) |

- PyTorch is developed at Meta — deepest integration
- Llama 4 family includes MoE variants with 128 total / 16 active expert routing
- Open-weight strategy means the training stack is well-documented
- FSDP (Fully Sharded Data Parallel) originated at Meta


### OpenAI (GPT-5 / o-Series / Codex)

| Aspect | Details |
|---|---|
| **Framework** | PyTorch (heavily customized) |
| **Parallelism** | TP + PP + DP, DeepSpeed-inspired sharding |
| **Orchestration** | Custom on Azure |
| **Hardware** | Azure NVIDIA clusters (H100 -> GB200 NVL72) |
| **Architecture** | Dense + MoE (details limited), reasoning chains (o-series) |
| **Notable** | Partnership with NVIDIA on GB200 NVL72 racks; Azure-exclusive |

- Heavily customized PyTorch fork (not vanilla)
- Deep Azure integration for scheduling, networking, storage
- GB200 NVL72 racks: 72 Blackwell GPUs per rack with NVLink interconnect
- o-series models use extended inference-time compute (chain-of-thought)


### Anthropic (Claude 4)

| Aspect | Details |
|---|---|
| **Framework** | PyTorch |
| **Parallelism** | DeepSpeed / ZeRO-based sharding |
| **Orchestration** | AWS-based clusters |
| **Hardware** | NVIDIA H100 / H200 on AWS (custom clusters) |
| **Architecture** | Dense + MoE elements, strong alignment focus |
| **Notable** | Constitutional AI methodology; AWS partnership; safety-first training |

- PyTorch + DeepSpeed on AWS infrastructure
- Heavy investment in alignment techniques (Constitutional AI, RLHF, iterative red-teaming)
- AWS custom clusters with high-bandwidth networking
- MoE elements incorporated into architecture


### Google DeepMind (Gemini 2.5+)

| Aspect | Details |
|---|---|
| **Framework** | JAX |
| **Parallelism** | Pathways (custom distributed runtime) |
| **Orchestration** | Borg / custom TPU scheduling |
| **Hardware** | TPU v5p / v6e + NVIDIA GPUs (hybrid) |
| **Architecture** | MoE, multimodal native |
| **Notable** | Pathways enables cross-pod TPU training; largest TPU deployments globally |

- JAX is developed at Google — deepest integration
- Pathways: distributed runtime that treats a TPU/GPU cluster as one virtual machine
- Hybrid TPU + GPU usage (TPU for training, GPUs for some inference)
- Natively multimodal architecture (text, image, video, audio, code)


## Comparison Table

| Company | Framework | Parallelism Stack | Hardware | Architecture | Cloud |
|---|---|---|---|---|---|
| **xAI** | JAX + Rust | DP+TP+PP, MoE | H100/H200 | MoE + RL | Custom DC |
| **Meta** | PyTorch | Megatron + FSDP + ZeRO | H100/H200 | Dense + MoE | On-prem |
| **OpenAI** | PyTorch (custom) | TP+PP+DP, DeepSpeed-style | H100 -> GB200 | Dense + MoE | Azure |
| **Anthropic** | PyTorch | DeepSpeed / ZeRO | H100/H200 | Dense + MoE | AWS |
| **Google** | JAX | Pathways | TPU v5p/v6e + GPU | MoE, multimodal | GCP |


## Why PyTorch + Megatron/DeepSpeed Dominates

- **Ecosystem size**: largest community, most libraries, most hiring pool
- **Megatron-Core**: battle-tested TP + PP + DP for large model training
- **DeepSpeed / ZeRO**: memory-efficient sharding without code changes
- **FSDP**: PyTorch-native sharding (originated at Meta, now standard)
- **NVIDIA integration**: CUDA, cuDNN, NCCL all optimized for PyTorch first
- **Flexibility**: easy to customize training loops, loss functions, architectures

Most frontier labs (OpenAI, Meta, Anthropic) use PyTorch because:
- The NVIDIA GPU ecosystem is built around it
- Hiring is easier (most ML engineers know PyTorch)
- Megatron-Core / DeepSpeed handle the hard distributed parts


## Why JAX Remains Strong at Google / xAI

- **XLA compiler**: whole-program optimization, better hardware utilization on TPUs
- **Functional paradigm**: easier to reason about parallelism (no mutable state)
- **Pathways**: Google's custom distributed runtime only works with JAX
- **TPU-native**: JAX is the first-class framework for TPU training
- **xAI connection**: key engineers from Google brought JAX expertise

JAX is not going away — it is the natural choice when:
- You control the hardware (Google TPUs, xAI custom clusters)
- You build custom distributed runtimes (Pathways)
- Your team has deep JAX/XLA expertise


## Framework Decision Matrix

| Factor | PyTorch | JAX |
|---|---|---|
| **Community size** | Very large | Smaller, concentrated |
| **GPU support** | First-class (CUDA/NCCL) | Good, but PyTorch is primary |
| **TPU support** | Via PyTorch/XLA (second-class) | First-class |
| **Distributed libraries** | Megatron, DeepSpeed, FSDP | Pathways, custom |
| **Debugging** | Eager mode (easy) | Compiled (harder) |
| **Hiring** | Easier (more engineers) | Harder (niche) |
| **Custom hardware** | Needs adapters | XLA compiles to any target |
| **Used by** | OpenAI, Meta, Anthropic | Google, xAI |


## TL;DR (Interview Summary)

- PyTorch + Megatron/DeepSpeed is the dominant stack (OpenAI, Meta, Anthropic)
- JAX + Pathways is the Google/xAI stack — strong but smaller ecosystem
- Every frontier lab uses MoE architectures in some form by early 2026
- NVIDIA GPUs (H100/H200/GB200) power most training; Google uses TPUs
- Meta open-sources Llama; OpenAI runs exclusively on Azure; Anthropic on AWS
- xAI built custom JAX + Rust infra with Kubernetes orchestration
- PyTorch dominates because of NVIDIA ecosystem, hiring pool, and library maturity
- JAX wins when you control the hardware (TPUs) or need whole-program compilation
