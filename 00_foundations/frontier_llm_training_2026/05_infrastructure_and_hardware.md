# 05 — Infrastructure and Hardware


## Cluster Scale

Frontier training in early 2026 operates at datacenter-scale:

- **Entry frontier**: ~10K–50K GPUs for a single training run
- **Mid frontier**: ~50K–200K GPUs (Meta, Anthropic, OpenAI scale)
- **Top frontier**: ~200K–1M+ GPUs (xAI Colossus, Google TPU pods, Meta fleet)

This is not shared infrastructure — these clusters are dedicated to single
training runs for weeks to months at a time.

### Notable deployments (publicly reported)

| Lab | Cluster | Scale | Notes |
|---|---|---|---|
| **xAI** | Colossus (Memphis) | 100K+ H100s, expanding toward 200K+ | Built in ~4 months; >1 GW power planned |
| **Meta** | Grand Teton clusters | 600K+ GPU fleet (H100/H200) | Largest reported fleet; split across runs |
| **OpenAI** | Azure clusters | Large (tens of thousands+) | Exclusive Azure partnership, GB200 NVL72 |
| **Anthropic** | AWS clusters | Tens of thousands of H100s | AWS partnership, custom networking |
| **Google** | TPU pods | v5p pods (8,960 chips), v6e scaling | Pathways spans multiple pods |


## GPU Evolution

NVIDIA dominates frontier training hardware. The progression:

### GPU Generations

| GPU | Release | HBM | FP16/BF16 TFLOPS | FP8 TFLOPS | Key Feature |
|---|---|---|---|---|---|
| **H100 SXM** | 2023 | 80 GB HBM3 | 989 | 1,979 | Transformer Engine, standard through 2025 |
| **H200 SXM** | 2024 | 141 GB HBM3e | 989 | 1,979 | More memory (same compute as H100) |
| **B200** | 2025 | 192 GB HBM3e | 2,250 | 4,500 | 2x H100 compute, FP8 native |
| **GB200 NVL72** | 2025 | 72 GPUs/rack, 13.5 TB total | ~1,400 per GPU | ~2,800 per GPU | Rack-scale NVLink, CPU+GPU integrated |

### GB200 NVL72 (Blackwell rack)

- 72 Blackwell GPUs + 36 Grace CPUs in a single rack
- All 72 GPUs connected via **NVLink** (1.8 TB/s per GPU)
- Acts as a single, massive "super-GPU"
- Eliminates intra-rack network bottleneck
- Targeted at frontier training and inference at scale


### Google TPUs

| TPU | Release | Memory | Notes |
|---|---|---|---|
| **v5p** | 2023 | 95 GB HBM | Pods of 8,960 chips, ICI interconnect |
| **v6e (Trillium)** | 2024 | 32 GB HBM | Higher efficiency, larger pods |

- TPU pods are connected via **ICI** (Inter-Chip Interconnect) — custom high-bandwidth mesh
- Google's Pathways runtime can span multiple pods


## GPU Requirements by Model Size

| Model Params | Active Params (if MoE) | GPUs Required (training) | Total GPU Memory | Example |
|---|---|---|---|---|
| 8B | 8B | 8–32 H100s | 0.6–2.5 TB | Llama 3.1 8B class |
| 70B | 70B | 128–512 H100s | 10–40 TB | Llama 3.1 70B class |
| 200B–400B | 200–400B (dense) | 1K–4K H100s | 80–320 TB | GPT-4 class (dense) |
| 400B+ (MoE) | 50–100B active | 2K–8K H100s | 160–640 TB | Llama 4 Maverick class |
| 1T+ (MoE) | 100–200B active | 10K–50K+ H100s | 800+ TB | Frontier MoE class |

**Notes**:
- Memory includes model weights + gradients + optimizer state + activations
- ZeRO/FSDP sharding reduces per-GPU memory requirements
- Actual cluster sizes are larger (include redundancy, checkpointing overhead)


## Power and Cooling

Frontier training clusters consume staggering amounts of power:

- **H100 SXM**: ~700W per GPU
- **B200**: ~1,000W per GPU
- **10K H100 cluster**: ~7 MW (GPUs alone) + networking + cooling = ~15–20 MW total
- **100K H100 cluster**: ~150–200 MW total facility power
- **xAI Colossus**: reported planning toward >1 GW total capacity

### Cooling

- **Air cooling**: standard up to ~40 kW per rack
- **Liquid cooling (direct-to-chip)**: required for Blackwell and dense GPU racks
  - GB200 NVL72 racks require liquid cooling — no air-cool option
  - ~120 kW per rack for NVL72
- All new frontier clusters being built in 2025–2026 use liquid cooling


## Interconnects

Training performance is bottlenecked by communication between GPUs.

| Interconnect | Scope | Bandwidth (per link) | Use |
|---|---|---|---|
| **NVLink** (4th gen) | GPU-to-GPU within node | 900 GB/s bidirectional | Tensor parallel within node |
| **NVLink** (5th gen, NVL72) | GPU-to-GPU within rack | 1.8 TB/s per GPU | Rack-scale tensor parallel |
| **NVSwitch** | All-to-all within node/rack | Enables full bisection | NVLink fabric switching |
| **InfiniBand NDR** | Node-to-node | 400 Gbps per port | Cross-node data parallel |
| **InfiniBand XDR** | Node-to-node | 800 Gbps per port | Next-gen cross-node (2025+) |
| **RoCE** (RDMA over Ethernet) | Node-to-node | 400 Gbps | Alternative to InfiniBand |
| **ICI** (Google) | TPU chip-to-chip | Custom high-bandwidth mesh | TPU pod interconnect |

### Key principle

- **Within a node**: NVLink (fast, low-latency) — use for tensor parallelism
- **Across nodes**: InfiniBand (slower, higher latency) — use for data parallelism
- The boundary between "fast" and "slow" interconnect determines how you partition parallelism


## TL;DR (Interview Summary)

- Frontier clusters: 10K–1M+ GPUs dedicated to single training runs
- GPU progression: H100 -> H200 -> B200 -> GB200 NVL72 (rack-scale NVLink)
- GB200 NVL72: 72 GPUs per rack, all NVLink-connected, liquid-cooled, ~120 kW
- 70B model: ~128–512 H100s; 1T MoE: ~10K–50K+ H100s
- Power: 100K GPU cluster = ~150–200 MW; xAI Colossus planning >1 GW
- Liquid cooling is mandatory for Blackwell-generation hardware
- NVLink within node (900 GB/s+), InfiniBand across nodes (400–800 Gbps)
- The interconnect topology determines how you partition parallelism strategies
