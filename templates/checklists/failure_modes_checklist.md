# Failure Modes Checklist

Common failure modes to discuss proactively in ML system design interviews.


## Model Failures

- [ ] Model performance degrades silently due to data drift
- [ ] Model produces confident but incorrect predictions on out-of-distribution inputs
- [ ] New model deployment introduces a regression caught only after rollout
- [ ] Model latency spikes under high concurrency or large input payloads


## Data Failures

- [ ] Upstream data source changes schema without notice
- [ ] Training data contains label noise or systematic bias
- [ ] Feature pipeline produces stale or missing features at serving time
- [ ] Data leakage between training and evaluation sets inflates offline metrics


## Infrastructure Failures

- [ ] Model server instance goes down; no failover in place
- [ ] Feature store read latency exceeds SLA during peak traffic
- [ ] Message queue backs up and causes delayed or dropped predictions
- [ ] Deployment pipeline pushes a broken model with no automated rollback


## LLM-Specific Failures

- [ ] LLM generates hallucinated or factually incorrect content
- [ ] Prompt injection causes the model to bypass safety guardrails
- [ ] Token budget exceeded for long inputs, causing truncated context
- [ ] Rate limits on external LLM API cause cascading timeouts in the serving path
