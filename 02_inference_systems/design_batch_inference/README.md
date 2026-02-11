# Design: Batch Inference

Design a system that runs model inference over large datasets offline, optimizing for throughput and cost rather than latency.


## Key Requirements

- Process millions to billions of records within a defined time window (e.g., nightly, hourly)
- Maximize hardware utilization with large batch sizes and parallel execution
- Provide exactly-once semantics with checkpointing and fault recovery


## Core Components

- Job orchestrator (Airflow, Spark, Ray) that partitions data and schedules inference workers
- Inference workers with large-batch GPU or CPU execution and dynamic batch sizing
- Checkpointing layer that tracks progress per partition for resumable execution on failure
- Output sink writing results to a feature store, data warehouse, or downstream queue
- Monitoring dashboard tracking throughput, cost, data quality, and SLA compliance per job


## Key Trade-offs

- Larger batches improve GPU utilization but increase memory pressure and checkpoint granularity
- Spot/preemptible instances cut cost 60-80% but require robust checkpointing and retry logic
- Pre-computing results avoids real-time latency but introduces staleness for time-sensitive features


## Must Explain in Interview

- When batch beats real-time: high volume, latency tolerance, cost sensitivity, precomputable outputs
- Checkpointing strategy: partition-level vs record-level, trade-off between recovery speed and overhead
- Spot instance handling: checkpointing frequency, graceful shutdown on preemption, retry queues
- Data partitioning: how to shard by key for parallelism while avoiding skew
- Freshness vs cost: how to choose batch frequency and when to add a real-time fallback path
