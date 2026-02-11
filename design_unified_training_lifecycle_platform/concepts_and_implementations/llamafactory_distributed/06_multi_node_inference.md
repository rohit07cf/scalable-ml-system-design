# 06 — Multi-Node Inference (LlamaFactory)


## When You Need Multi-Node Inference

- **Throughput**: one machine can't handle the request volume
- **Availability**: multiple replicas for failover
- **Cost**: spread load across cheaper machines with fewer GPUs

The default pattern: **data parallel replicas behind a load balancer**.


## Architecture

```
                 ┌──────────────────┐
                 │   Load Balancer  │
                 │ (nginx, HAProxy, │
                 │  K8s Ingress)    │
                 └────────┬─────────┘
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Node 0  │ │  Node 1  │ │  Node 2  │
        │  (vLLM)  │ │  (vLLM)  │ │  (vLLM)  │
        │  replica │ │  replica │ │  replica │
        │  port    │ │  port    │ │  port    │
        │  8000    │ │  8000    │ │  8000    │
        └──────────┘ └──────────┘ └──────────┘
```

- Each node runs an **independent** LlamaFactory/vLLM server
- No communication between nodes during inference
- Load balancer distributes requests
- Any node can die without taking down the whole service


## Horizontal Scaling — Key Points

### Each replica is independent

- No shared state between replicas
- No distributed communication (unlike training)
- Each node loads the model from shared storage (S3, NFS)
- Scaling = add more nodes behind the load balancer

### Shared model artifacts

All nodes pull the same model weights from a shared source:

```
┌─────────┐     pull on startup     ┌──────────┐
│   S3    │ ──────────────────────> │  Node N  │
│  (model │                         │  (local  │
│  store) │                         │   copy)  │
└─────────┘                         └──────────┘
```

- Model downloaded once per node on startup
- Cache locally to avoid re-downloading on restart
- All nodes serve the same model version


### Load balancer strategies

| Strategy | How it works | When to use |
|---|---|---|
| **Round-robin** | Alternate between nodes | Equal capacity nodes |
| **Least-connections** | Send to node with fewest active requests | Varying request sizes |
| **Health-check based** | Skip unhealthy nodes | Always (baseline) |


## Multi-Node Run Approach

### Step 1: Deploy model to shared storage

```bash
# Upload model once
aws s3 sync ./merged_model s3://models/llama-3-8b-support/
```

### Step 2: Launch on each node

```bash
# Same command on every node (or in each K8s pod)
llamafactory-cli api configs/inference_multi_node.yaml
```

Config:

```yaml
model_name_or_path: /models/llama-3-8b-support  # local cache path
template: llama3
infer_backend: vllm
vllm_maxlen: 4096
```

### Step 3: Load balancer config (nginx example)

```nginx
upstream llm_backend {
    least_conn;
    server node0:8000;
    server node1:8000;
    server node2:8000;
}

server {
    listen 80;
    location /v1/ {
        proxy_pass http://llm_backend;
    }
}
```

### In Kubernetes

```yaml
# Simplified K8s mental model
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference
spec:
  replicas: 3                    # 3 independent replicas
  template:
    spec:
      containers:
      - name: vllm
        image: llm-serving:latest
        command: ["llamafactory-cli", "api", "configs/inference.yaml"]
        resources:
          limits:
            nvidia.com/gpu: 1    # 1 GPU per replica
---
apiVersion: v1
kind: Service                    # load balances across replicas
metadata:
  name: llm-service
spec:
  selector:
    app: llm-inference
  ports:
  - port: 8000
```


## Client Sends Request

The client doesn't know (or care) which node handles the request:

```python
import requests

# Client talks to load balancer, not individual nodes
response = requests.post("http://llm-service:8000/v1/chat/completions", json={
    "model": "llama-3-8b-support",
    "messages": [
        {"role": "user", "content": "My order arrived damaged. What should I do?"}
    ],
    "max_tokens": 200,
})

print(response.json()["choices"][0]["message"]["content"])
```

See `python/minimal_inference_client.py` for streaming support.


## Scaling Up vs Scaling Out

| | Scale up (bigger machine) | Scale out (more machines) |
|---|---|---|
| Approach | More GPUs per node, tensor parallel | More nodes, data parallel |
| When | Model needs multiple GPUs | Need more throughput |
| Limit | Max GPUs per machine (typically 8) | Budget / cluster size |
| Complexity | Low (one machine) | Medium (load balancer, health checks) |

**Typical production pattern**: scale up within a node (TP for large models),
then scale out across nodes (DP replicas) for throughput.


## Failure Handling

- **Node dies**: load balancer health check detects it → stops routing
  - Other nodes continue serving
  - K8s restarts the failed pod automatically

- **Model loading slow**: use readiness probes
  - Node only receives traffic AFTER the model is loaded

- **Uneven load**: use least-connections balancing
  - Nodes with long-running requests get fewer new requests


## Common Traps

- **Tensor parallel across nodes** → DON'T. Network latency per layer
  makes this impractical. Use TP within a node, DP across nodes.

- **No health checks on the load balancer** → requests go to dead nodes
  → user-facing errors.

- **Not pre-pulling model weights** → first request waits minutes
  while the model downloads. Use an init container or startup probe.

- **Different model versions on different nodes** → inconsistent responses.
  Pin the model artifact version; roll out new versions with blue-green deploy.


## TL;DR (Interview Summary)

- Multi-node inference = independent replicas behind a load balancer
- No communication between nodes — each is a standalone vLLM server
- Shared model artifacts from S3/NFS — all nodes serve the same version
- Load balancer: least-connections + health checks is the production default
- Scale out linearly: 3 nodes = ~3× throughput
- In K8s: Deployment with N replicas + Service for load balancing
- Never do tensor parallel across nodes — network latency kills it
- Client talks to the load balancer — doesn't know which node serves it
