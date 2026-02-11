# 05 — Single-Node Multi-GPU Inference (LlamaFactory)


## What This Covers

- Running inference with multiple GPUs on **one machine**
- Two modes: data parallel (replicas) or tensor parallel (split model)
- Where batching happens and how to scale


## Two Approaches

### Approach 1: Data Parallel — separate replicas

```
GPU 0: [Full model replica A]  → handles requests 1, 3, 5
GPU 1: [Full model replica B]  → handles requests 2, 4, 6
```

- When: model fits on 1 GPU (e.g., 7B on A100)
- Pro: simple, linear throughput scaling, no communication overhead
- Con: each GPU needs full model + KV cache memory

### Approach 2: Tensor Parallel — split one model

```
GPU 0: [Model layers — first half]  ─┐
                                       ├── work together on every request
GPU 1: [Model layers — second half] ─┘
```

- When: model is too large for 1 GPU (e.g., 70B)
- Pro: can serve models that don't fit on one GPU
- Con: GPUs communicate at every layer (NVLink needed)


## LlamaFactory Inference (API Server Mode)

LlamaFactory can launch an OpenAI-compatible API server:

```bash
# Single-node, multi-GPU inference (uses vLLM backend)
llamafactory-cli api \
    configs/inference_single_node.yaml
```

See `configs/inference_single_node.yaml` for full config.

Key settings:

```yaml
model_name_or_path: meta-llama/Llama-3.1-8B-Instruct
template: llama3
infer_backend: vllm           # vLLM for production serving

# vLLM settings
vllm_enforce_eager: false     # enable CUDA graphs for speed
vllm_maxlen: 4096             # max sequence length
```

vLLM auto-detects GPUs:
- If model fits on 1 GPU → runs 1 instance per GPU (data parallel via separate workers)
- If model needs N GPUs → tensor parallelism across N GPUs


### Explicit tensor parallel (for large models)

```yaml
# 70B model across 4 GPUs
model_name_or_path: meta-llama/Llama-3.1-70B-Instruct
vllm_tensor_parallel_size: 4  # split model across 4 GPUs
```


## Where Batching Happens

```
Client requests
      │
      ▼
┌──────────────┐
│  API Server  │  (FastAPI / OpenAI-compatible)
│  receives    │
│  requests    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  vLLM Engine │  ← continuous batching happens HERE
│  • groups requests into batches
│  • manages KV cache memory
│  • prefill + decode scheduling
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  GPU(s)      │  ← actual computation
│  run the     │
│  model       │
└──────────────┘
```

- **You don't manage batching** — vLLM's scheduler handles it
- vLLM uses PagedAttention for efficient KV cache management
- New requests are added to the batch continuously


## Scaling Replicas (Data Parallel)

For small-to-medium models that fit on 1 GPU, run multiple replicas:

**Option A: Multiple processes behind a reverse proxy**

```bash
# Terminal 1: replica on GPU 0
CUDA_VISIBLE_DEVICES=0 llamafactory-cli api configs/inference_single_node.yaml --port 8000

# Terminal 2: replica on GPU 1
CUDA_VISIBLE_DEVICES=1 llamafactory-cli api configs/inference_single_node.yaml --port 8001
```

Then put an nginx/HAProxy load balancer in front.

**Option B: Let vLLM handle it**

vLLM can internally manage multiple GPU workers for data parallelism.
This is simpler — one process, one port.


## Client Call (Minimal)

```python
import requests

response = requests.post("http://localhost:8000/v1/chat/completions", json={
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "My order is late."}],
    "max_tokens": 200,
    "temperature": 0.7,
})

print(response.json()["choices"][0]["message"]["content"])
```

See `python/minimal_inference_client.py` for streaming example.


## Common Traps

- **Using too many GPUs for tensor parallel on a small model**
  — overhead of GPU communication > benefit. Don't TP a 7B model across 4 GPUs.

- **Not setting `max_model_len` / `vllm_maxlen`** → vLLM pre-allocates
  KV cache for the model's maximum context length, eating all memory.

- **Running multiple vLLM instances on overlapping GPUs**
  → OOM. Use `CUDA_VISIBLE_DEVICES` to isolate.


## TL;DR (Interview Summary)

- Single-node multi-GPU inference: data parallel (replicas) or tensor parallel (split model)
- Data parallel for models that fit on 1 GPU — simple, linear scaling
- Tensor parallel for large models (70B+) — needs NVLink between GPUs
- LlamaFactory + vLLM handles batching and KV cache automatically
- vLLM's continuous batching = production-grade throughput without manual tuning
- Set `vllm_maxlen` to control KV cache memory allocation
- Client talks to an OpenAI-compatible API — standard request/response format
- Start with the simplest setup; add tensor parallel only when the model demands it
