# Design: Edge Inference

Design a system that runs ML models on-device (mobile, IoT, browser) with constrained compute, memory, and connectivity.


## Key Requirements

- Run inference on devices with limited resources (e.g., 2-4GB RAM, mobile NPU/GPU)
- Operate offline or with intermittent connectivity, with graceful cloud fallback
- Update models over-the-air without breaking existing device functionality


## Core Components

- Model compression pipeline: distillation, pruning, quantization (INT8/INT4) targeting device hardware
- On-device runtime (TFLite, CoreML, ONNX Mobile, or MLC-LLM) matched to device capabilities
- Edge-cloud routing layer that decides local vs cloud inference based on model confidence and connectivity
- OTA model update service with versioning, staged rollouts, and rollback support
- On-device telemetry collector for latency, accuracy drift, and crash reporting


## Key Trade-offs

- Smaller models run fast on-device but sacrifice accuracy compared to server-side models
- On-device inference eliminates network latency but limits model complexity
- OTA updates add deployment flexibility but require robust versioning to avoid bricking devices


## Must Explain in Interview

- Model compression chain: how distillation, pruning, and quantization compose and their accuracy impact
- Hardware-aware optimization: why the same model runs differently on ARM CPU vs mobile GPU vs NPU
- Offline-first architecture: local inference with sync-when-connected for logging and model updates
- OTA rollout strategy: canary on device cohorts, automatic rollback triggers, A/B testing on-device
- Privacy considerations: what data stays on-device vs what telemetry is sent to the cloud
