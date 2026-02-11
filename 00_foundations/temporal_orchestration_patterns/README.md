# Temporal Orchestration Patterns


## 1. Why Temporal for ML/LLM Platforms

- ML pipelines are multi-step and long-running -- fine-tuning takes hours, eval takes minutes, ingestion runs continuously
- Steps fail frequently -- GPU OOM, API timeouts, network errors, rate limits
- Temporal gives you retries, resume-from-failure, and durable state without custom infrastructure
- Each workflow execution is conceptually exactly-once -- Temporal deduplicates by workflow ID
- Better than "queue + worker" for complex pipelines because you get orchestration, not just dispatch

Without Temporal (or similar), you end up building retry logic, state tracking, dead-letter handling, and crash recovery yourself. That is a platform, not application code.


## 2. Temporal Building Blocks (Interview Definition)

- **Workflow** -- a durable function that orchestrates activities; survives crashes and restarts via replay
- **Activity** -- a single unit of work with side effects (API call, GPU inference, file write); the thing that actually does work
- **Worker** -- a long-running process that polls a task queue and executes workflows or activities
- **Task Queue** -- a named queue that connects workflow/activity dispatches to workers polling that queue
- **Workflow Execution** -- a running instance of a workflow, identified by a unique workflow ID


## 3. Reliability Guarantees You Get "For Free"

- **Durable state** -- workflow progress is persisted by Temporal server; your code does not manage state
- **Automatic retries** -- activities retry on failure with configurable backoff, max attempts, and timeout
- **Replay model** -- on worker restart, Temporal replays the workflow history to reconstruct state; completed activities are not re-executed
- **Resume after crash** -- if a worker crashes mid-workflow, another worker picks up from the last completed activity
- **Long-running safety** -- workflows can run for days or weeks; heartbeats detect stuck activities

You write the happy path. Temporal handles the failure path.


## 4. Timeouts, Retries, Heartbeats (Practical Defaults)

**Timeouts:**

- **Start-to-close timeout** -- max time an activity can run from start to completion (e.g., 300s for inference, 3600s for training)
- **Schedule-to-start timeout** -- max time an activity can wait in the task queue before a worker picks it up (e.g., 60s); detects capacity problems
- **Schedule-to-close timeout** -- total budget from dispatch to completion; covers both queue wait and execution

**Retries:**

- **Initial interval** -- first retry delay (e.g., 1s)
- **Backoff coefficient** -- multiplier per retry (e.g., 2.0 for exponential backoff)
- **Max attempts** -- hard limit on retries (e.g., 3-5 for inference, 2 for training)
- **Non-retryable errors** -- list of error types that should fail immediately (e.g., validation errors)

**Heartbeats:**

- Long-running activities send periodic heartbeats to Temporal (e.g., every 30s)
- If heartbeat stops, Temporal considers the activity failed and retries it
- Use for: fine-tuning jobs, large batch embeddings, long inference chains
- Heartbeat can carry progress data -- on retry, the activity can resume from the last reported position


## 5. Multi-Queue Architecture (CPU vs GPU)

Different activities need different resources. Routing them through separate task queues keeps resource pools isolated.

**Why separate queues:**

- CPU work (validation, preprocessing) should not block GPU work (inference, training)
- GPU workers are expensive -- do not waste them on CPU-bound tasks
- Each queue is an independent scaling knob -- scale CPU and GPU workers separately
- Prevents GPU starvation when a burst of CPU tasks arrives

**Architecture:**

```
Workflow (orchestrator)
  |
  |-- validate_input()    --> [cpu-queue] --> CPU Workers
  |-- preprocess()        --> [cpu-queue] --> CPU Workers
  |-- run_inference()     --> [gpu-queue] --> GPU Workers
  |-- compute_embeddings()--> [gpu-queue] --> GPU Workers
```

The workflow itself runs on any worker. It dispatches each activity to the correct task queue. Workers only poll the queues they are configured for.


## 6. Multi-Worker Architecture (How it Scales)

- Multiple worker processes can poll the same task queue -- this is horizontal scaling
- Workers are stateless -- any worker polling a queue can pick up any task on that queue
- Workers specialize by resource type:
  - **CPU workers** -- run on standard compute; handle validation, preprocessing, I/O
  - **GPU workers** -- run on GPU nodes; handle inference, training, embedding

**Scaling approach:**

- Monitor queue backlog (pending tasks per queue)
- Scale CPU workers independently from GPU workers
- In Kubernetes: use HPA (Horizontal Pod Autoscaler) based on queue depth metrics
- GPU workers scale slower (node provisioning) -- keep a warm pool for latency-sensitive work

**Concurrency control:**

- Each worker has a configurable max concurrent activity count
- Prevents a single worker from accepting more work than its resources can handle
- GPU workers typically run fewer concurrent activities (1-4) than CPU workers (10-50)


## 7. Multi-Workflow Architecture (Why it Matters)

Different products need different orchestration logic. Each gets its own workflow type.

**Examples:**

- `PrepareAndInferWorkflow` -- validate, preprocess, run inference
- `BatchEmbedWorkflow` -- preprocess batch, compute embeddings
- `FineTuneWorkflow` -- validate dataset, upload, train, evaluate
- `DocumentIngestWorkflow` -- chunk, embed, index into vector store
- `EvalWorkflow` -- run test suite, score, compare against baseline

**Benefits:**

- Each workflow has its own retry policy, timeout configuration, and error handling
- Workflows route activities to different task queues based on resource needs
- Separation of concerns -- changes to ingestion do not affect inference
- Different teams can own different workflows independently


## 8. Temporal Factory Pattern (Routing + Registration)

A factory centralizes workflow registration and routing. Instead of hardcoding workflow starts throughout your application, you go through a single entry point.

**Components:**

- **Registry** -- maps workflow name (string) to workflow class
- **Router** -- maps workflow name to task queue
- **start_workflow(name, input)** -- looks up the correct workflow class and task queue, then starts the execution

**Why this helps in an enterprise platform:**

- Config-driven execution -- add new workflows by updating the registry, not application code
- Central enforcement of policies -- timeouts, retries, idempotency keys applied in one place
- Safe routing -- the factory validates workflow name and input before starting
- Supports multiple workflows without scattered Temporal client calls

**Trade-off:** adds a layer of indirection. Worth it when you have more than 2-3 workflow types. Overkill for a single workflow.


## 9. Elementary Example (End-to-End)

**"Mini AI Pipeline"** -- two workflows, two queues, two worker types, one factory.

**Workflow A: PrepareAndInferWorkflow**

1. `validate_input(text)` -- CPU queue -- checks input is non-empty, within token limit
2. `preprocess(text)` -- CPU queue -- normalizes whitespace, strips special characters
3. `run_inference(clean_text)` -- GPU queue -- runs model inference, returns result

**Workflow B: BatchEmbedWorkflow**

1. `preprocess_batch(texts)` -- CPU queue -- normalizes a list of texts
2. `compute_embeddings(clean_texts)` -- GPU queue -- computes embedding vectors

**Flow diagram:**

```
Client
  |
  v
WorkflowFactory.start_workflow("prepare_and_infer", {"text": "..."})
  |
  v
PrepareAndInferWorkflow
  |-- validate_input(text)      --> [cpu-queue] --> CPU Worker
  |-- preprocess(text)          --> [cpu-queue] --> CPU Worker
  |-- run_inference(clean_text) --> [gpu-queue] --> GPU Worker
  |
  v
Result returned to caller


Client
  |
  v
WorkflowFactory.start_workflow("batch_embed", {"texts": [...]})
  |
  v
BatchEmbedWorkflow
  |-- preprocess_batch(texts)         --> [cpu-queue] --> CPU Worker
  |-- compute_embeddings(clean_texts) --> [gpu-queue] --> GPU Worker
  |
  v
Result returned to caller
```


## 10. Reference Python Implementation (Minimal)

### Constants and imports

```python
# shared.py
import asyncio
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.common import RetryPolicy

CPU_TASK_QUEUE = "cpu-queue"
GPU_TASK_QUEUE = "gpu-queue"
```

### Activities

```python
# activities.py
from shared import activity

# --- CPU activities (run on cpu-queue workers) ---

@activity.defn
async def validate_input(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("Input text is empty")
    if len(text) > 10000:
        raise ValueError("Input text exceeds token limit")
    return text.strip()

@activity.defn
async def preprocess(text: str) -> str:
    clean = " ".join(text.split())  # normalize whitespace
    return clean.lower()

@activity.defn
async def preprocess_batch(texts: list[str]) -> list[str]:
    return [" ".join(t.split()).lower() for t in texts if t.strip()]

# --- GPU activities (run on gpu-queue workers) ---

@activity.defn
async def run_inference(clean_text: str) -> dict:
    # Placeholder: real implementation calls a model
    await asyncio.sleep(2)  # simulate GPU inference latency
    return {"input": clean_text, "label": "positive", "score": 0.95}

@activity.defn
async def compute_embeddings(clean_texts: list[str]) -> list[list[float]]:
    # Placeholder: real implementation calls an embedding model
    await asyncio.sleep(3)  # simulate GPU batch embedding
    return [[0.1, 0.2, 0.3] for _ in clean_texts]
```

### Workflows

```python
# workflows.py
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import (
        validate_input, preprocess, run_inference,
        preprocess_batch, compute_embeddings,
    )
    from shared import CPU_TASK_QUEUE, GPU_TASK_QUEUE

CPU_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

GPU_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_attempts=2,
)

@workflow.defn
class PrepareAndInferWorkflow:
    @workflow.run
    async def run(self, text: str) -> dict:
        validated = await workflow.execute_activity(
            validate_input,
            text,
            task_queue=CPU_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=CPU_RETRY,
        )
        cleaned = await workflow.execute_activity(
            preprocess,
            validated,
            task_queue=CPU_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=CPU_RETRY,
        )
        result = await workflow.execute_activity(
            run_inference,
            cleaned,
            task_queue=GPU_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=GPU_RETRY,
            heartbeat_timeout=timedelta(seconds=30),
        )
        return result


@workflow.defn
class BatchEmbedWorkflow:
    @workflow.run
    async def run(self, texts: list[str]) -> list[list[float]]:
        cleaned = await workflow.execute_activity(
            preprocess_batch,
            texts,
            task_queue=CPU_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=CPU_RETRY,
        )
        embeddings = await workflow.execute_activity(
            compute_embeddings,
            cleaned,
            task_queue=GPU_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=300),
            retry_policy=GPU_RETRY,
            heartbeat_timeout=timedelta(seconds=30),
        )
        return embeddings
```

### Workflow Factory

```python
# factory.py
from temporalio.client import Client

from shared import CPU_TASK_QUEUE, GPU_TASK_QUEUE
from workflows import PrepareAndInferWorkflow, BatchEmbedWorkflow

WORKFLOW_REGISTRY = {
    "prepare_and_infer": PrepareAndInferWorkflow,
    "batch_embed": BatchEmbedWorkflow,
}

QUEUE_ROUTER = {
    "prepare_and_infer": CPU_TASK_QUEUE,
    "batch_embed": CPU_TASK_QUEUE,
}
# Note: queue_router maps to the queue where the WORKFLOW runs.
# Activities within each workflow route themselves to cpu/gpu queues.


class WorkflowFactory:
    def __init__(self, client: Client):
        self.client = client

    async def start_workflow(self, name: str, input_data, workflow_id: str):
        if name not in WORKFLOW_REGISTRY:
            raise ValueError(f"Unknown workflow: {name}")

        workflow_class = WORKFLOW_REGISTRY[name]
        task_queue = QUEUE_ROUTER[name]

        handle = await self.client.start_workflow(
            workflow_class.run,
            input_data,
            id=workflow_id,
            task_queue=task_queue,
        )
        return handle
```

### Workers

```python
# worker_cpu.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from shared import CPU_TASK_QUEUE
from workflows import PrepareAndInferWorkflow, BatchEmbedWorkflow
from activities import validate_input, preprocess, preprocess_batch

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue=CPU_TASK_QUEUE,
        workflows=[PrepareAndInferWorkflow, BatchEmbedWorkflow],
        activities=[validate_input, preprocess, preprocess_batch],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

```python
# worker_gpu.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from shared import GPU_TASK_QUEUE
from activities import run_inference, compute_embeddings

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue=GPU_TASK_QUEUE,
        # GPU worker only runs activities, not workflows
        activities=[run_inference, compute_embeddings],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Client runner

```python
# run_client.py
import asyncio
import uuid
from temporalio.client import Client
from factory import WorkflowFactory

async def main():
    client = await Client.connect("localhost:7233")
    factory = WorkflowFactory(client)

    # Start inference workflow
    handle = await factory.start_workflow(
        "prepare_and_infer",
        "  Hello world, this is a test input!  ",
        workflow_id=f"infer-{uuid.uuid4()}",
    )
    result = await handle.result()
    print(f"Inference result: {result}")

    # Start batch embed workflow
    handle = await factory.start_workflow(
        "batch_embed",
        ["first document", "second document", "third document"],
        workflow_id=f"embed-{uuid.uuid4()}",
    )
    result = await handle.result()
    print(f"Embeddings: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### How to run

- Start Temporal server: `temporal server start-dev`
- Start CPU worker: `python worker_cpu.py`
- Start GPU worker: `python worker_gpu.py`
- Run client: `python run_client.py`


## 11. Common Failure Scenarios + What Happens

**CPU worker crashes mid-activity:**
Temporal detects the worker is gone (task times out or heartbeat stops). The activity is retried on another available CPU worker from the beginning. Completed prior activities are not re-executed.

**GPU worker crashes mid-activity (heartbeat):**
Heartbeat stops arriving. Temporal marks the activity as failed after heartbeat timeout expires. The activity is retried on another GPU worker. If the activity reported progress via heartbeat data, the retry can resume from that checkpoint.

**Activity times out (start-to-close):**
Temporal cancels the activity and retries according to the retry policy. If max attempts are exhausted, the workflow receives the error and can handle it (fail, fallback, or compensate).

**Workflow worker restarts:**
Temporal replays the workflow history on the new worker. All previously completed activities are skipped (their results are replayed from history). Execution continues from where it left off. No duplicate side effects.

**Duplicate start requests:**
If you start a workflow with the same workflow ID, Temporal rejects the duplicate by default. This gives you idempotent workflow starts without extra code. Use deterministic workflow IDs (e.g., `ingest-{document_id}`) to prevent duplicates.


## 12. Interview Q&A

**Why use Temporal instead of a simple queue + worker?**
A queue dispatches tasks but does not orchestrate them. Temporal tracks multi-step workflow state, retries individual steps, resumes after crashes, and replays history. You get orchestration, not just dispatch.

**How do retries work in Temporal?**
Each activity has a retry policy (initial interval, backoff coefficient, max attempts). On failure, Temporal re-dispatches the activity to the task queue. Workers are stateless -- any worker polling that queue can execute the retry.

**What is workflow replay?**
When a workflow worker restarts, Temporal sends the full event history to the new worker. The workflow code re-executes, but completed activities return cached results from history instead of re-running. This reconstructs workflow state without side effects.

**Why separate CPU and GPU task queues?**
GPU workers are expensive and scarce. Mixing CPU and GPU work on one queue means CPU tasks could block GPU tasks or waste GPU resources. Separate queues let you scale and prioritize each resource pool independently.

**How do you scale workers?**
Add more worker processes polling the same task queue. Workers are stateless, so horizontal scaling is straightforward. In Kubernetes, autoscale based on queue backlog depth per queue.

**How do you prevent duplicate workflow starts?**
Use deterministic workflow IDs derived from the input (e.g., `finetune-{job_id}`). Temporal rejects a start request if a workflow with that ID is already running. This is built-in idempotency.

**How do you handle long-running GPU tasks safely?**
Use heartbeats. The activity sends periodic heartbeats to Temporal. If the heartbeat stops (worker crash, OOM), Temporal marks the activity as failed and retries it. Heartbeat data can carry progress for checkpoint-based resume.

**What is the Temporal Factory pattern?**
A registry that maps workflow names to workflow classes and task queues. A single `start_workflow(name, input)` method looks up the correct workflow and queue. Centralizes routing, validation, and policy enforcement.

**What happens if the Temporal server itself goes down?**
Workers cannot poll tasks, so in-flight dispatches stall. But workflow state is durably persisted. When the server recovers, workflows resume from their last recorded state. No data is lost.

**Why register workflows on the CPU worker but not the GPU worker?**
Workflows are orchestration logic (lightweight, CPU-bound). They dispatch activities to the correct queues. GPU workers only need to run GPU activities. This keeps GPU workers focused on compute, not orchestration overhead.

**What is the difference between start-to-close and schedule-to-start timeout?**
Start-to-close is how long the activity can execute. Schedule-to-start is how long it can wait in the queue before a worker picks it up. A schedule-to-start timeout detects capacity problems (no workers available).

**When would you NOT use Temporal?**
For simple, single-step, fire-and-forget tasks where a basic queue (SQS, Redis) is sufficient. Temporal adds operational complexity (server, persistence). Use it when you need multi-step orchestration, durable state, or complex retry logic.


## 13. Fast Revision Summary

- Temporal gives you durable orchestration: retries, resume, replay, and long-running safety without custom code
- A workflow orchestrates; an activity does the work; a worker executes both; a task queue connects them
- Separate CPU and GPU task queues to isolate resource pools and scale independently
- Workers are stateless -- horizontal scaling means adding more workers polling the same queue
- Each workflow type has its own retry policy, timeout config, and task queue routing
- The factory pattern centralizes workflow registration, routing, and policy enforcement
- Heartbeats detect stuck long-running activities; heartbeat data enables checkpoint-based resume
- Workflow replay reconstructs state from history -- completed activities are not re-executed
- Deterministic workflow IDs give you built-in idempotency for free
- Temporal is worth the operational cost when pipelines are multi-step, long-running, or failure-prone
