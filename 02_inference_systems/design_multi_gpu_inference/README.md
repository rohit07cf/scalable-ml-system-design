# Design: Multi-GPU Inference

Design a serving system that distributes large model inference across multiple GPUs to meet latency and throughput targets.


## Key Requirements

- Serve models too large for a single GPU (e.g., 70B+ parameter LLMs)
- P99 latency under 500ms for real-time requests at thousands of QPS
- Maximize GPU utilization while minimizing cost per request


## Core Components

- Load balancer with model-aware routing and health checks
- Model parallelism layer: tensor parallel across GPUs within a node, pipeline parallel across nodes
- Continuous batching engine (e.g., vLLM, TensorRT-LLM) to maximize throughput
- KV cache management with paged attention for memory efficiency
- Autoscaler monitoring GPU utilization, queue depth, and latency percentiles


## Key Trade-offs

- Tensor parallelism reduces latency but requires high-bandwidth interconnects (NVLink)
- Larger batch sizes improve throughput but increase tail latency
- Quantization (INT8/INT4) cuts memory and cost but may degrade output quality


## Must Explain in Interview

- Why tensor parallelism needs NVLink and how pipeline parallelism works across nodes
- How continuous batching differs from static batching and why it matters for LLMs
- How KV cache and paged attention prevent memory fragmentation during generation
- Autoscaling signals: why GPU utilization alone is insufficient (queue depth, TTFT matter)
- Cost model: how to calculate cost-per-token and compare against API providers
