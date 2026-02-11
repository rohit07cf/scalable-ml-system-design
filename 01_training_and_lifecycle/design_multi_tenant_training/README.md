# Design: Multi-Tenant Training Platform

Design a shared training platform where multiple teams submit, schedule, and monitor training jobs with resource isolation, fair scheduling, and cost attribution.


## Key Requirements

- Isolate tenants' data, code, and compute so one team cannot access or disrupt another
- Fairly schedule GPU/CPU resources across teams with quotas, priorities, and preemption policies
- Provide per-tenant cost tracking, usage dashboards, and chargeback reporting


## Core Components

- Job submission API -- accepts training specs (image, resources, data refs), validates quotas
- Scheduler -- fair-share or priority-based GPU allocation (Kubernetes + gang scheduling for multi-node)
- Namespace isolation -- separate Kubernetes namespaces, RBAC, network policies, encrypted storage per tenant
- Resource manager -- enforces quotas, handles spot/preemptible instances, manages GPU fragmentation
- Observability layer -- per-tenant metrics (GPU utilization, queue wait, cost), Prometheus + Grafana


## Key Trade-Offs

- Strict namespace isolation vs shared storage: security vs data dedup and storage cost
- Fair-share scheduling vs priority queues: equality vs letting critical teams jump the line
- Dedicated GPU pools per team vs shared elastic pool: predictable capacity vs higher overall utilization


## Must Explain in Interview

- How Kubernetes namespaces + RBAC enforce tenant isolation for training workloads
- Gang scheduling: why multi-GPU jobs must get all GPUs atomically or not at all
- Quota design: guaranteed vs burst capacity per team, with preemption of burst jobs when demand spikes
- GPU fragmentation: why 3 free GPUs across 3 nodes cannot serve a 3-GPU job needing NVLink
- Cost attribution: track GPU-hours per job, tag by team/project, aggregate for monthly chargeback
