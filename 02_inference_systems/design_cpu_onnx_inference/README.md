# Design: CPU + ONNX Inference

Design a cost-efficient serving system that runs ML models on CPUs using ONNX Runtime for workloads where GPU cost is not justified.


## Key Requirements

- Serve small-to-medium models (embeddings, classifiers, rankers) at sub-50ms P99 latency
- Run on commodity CPU instances to reduce infrastructure cost by 5-10x vs GPU
- Support multiple model formats converted to a single optimized runtime


## Core Components

- ONNX Runtime serving layer with graph optimizations and operator fusion
- Model conversion pipeline: PyTorch/TF to ONNX with validation checks
- Dynamic batching proxy that groups concurrent requests for throughput
- Horizontal autoscaler based on CPU utilization and request queue length
- Model registry tracking ONNX artifacts, input/output schemas, and performance benchmarks


## Key Trade-offs

- CPUs handle small models cheaply but hit a wall on large transformers (latency degrades fast)
- ONNX quantization (INT8) improves speed but requires calibration data and accuracy validation
- Fewer hardware dependencies vs GPU, but less community tooling for large model optimization


## Must Explain in Interview

- When CPU inference is the right choice: model size thresholds, latency budgets, cost targets
- ONNX graph optimizations: constant folding, operator fusion, and how they reduce latency
- How dynamic batching on CPU differs from GPU batching (no CUDA streams, memory layout matters)
- Quantization workflow: calibration dataset, accuracy regression testing, rollback strategy
- Comparison framework: cost-per-request on CPU vs GPU for the same model and SLA
