# Inference Systems


## What This Section Covers

- Serving ML and LLM models at scale under latency and cost constraints
- Hardware-aware deployment: GPU, CPU, edge, and serverless targets
- Batch vs real-time inference trade-offs and architecture patterns
- Optimization techniques: quantization, batching, caching, model parallelism


## What Interviewers Usually Test

- Can you design an end-to-end serving stack with clear latency/throughput targets?
- Do you understand the hardware and cost implications of your choices?
- Can you articulate when to use batch vs real-time vs serverless?


## Suggested Study Order

1. `design_multi_gpu_inference` -- foundational GPU serving patterns
2. `design_cpu_onnx_inference` -- cost-efficient CPU deployment
3. `design_batch_inference` -- offline and high-throughput workloads
4. `design_serverless_inference` -- event-driven and spiky traffic
5. `design_edge_inference` -- on-device and constrained environments


## Fast Revision Path

- Re-read "Must explain in interview" in each subfolder
- Review the latency vs throughput vs cost triangle for each design
- Practice drawing one HLD from memory in under 5 minutes
