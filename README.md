# ML System Design Interview Prep

A structured, scannable reference for ML + LLM system design interviews.


## What This Repo Is

- Interview-focused ML system design reference
- Covers training, inference, RAG, agents, eval, platform, recs, and end-to-end cases
- Organized for fast recall, not academic completeness
- Each use case follows a consistent 7-phase template
- Built for 2-3 minute skims per topic


## How to Revise in 30 Minutes

- Pick 2-3 use cases you expect in the interview
- Skim the "Must explain in interview" section in each
- Review the template phases (requirements, estimation, HLD, deep dives)
- Glance at the checklists in `templates/checklists/`
- Do one full mock walkthrough out loud


## Folder Overview

| Folder | Focus |
|---|---|
| `00_foundations` | Core concepts: LLMs, latency, eval, reliability, orchestration |
| `01_training_and_lifecycle` | Fine-tuning, HPO, retraining, RLHF |
| `02_inference_systems` | Multi-GPU, CPU, edge, serverless, batch |
| `03_retrieval_and_rag` | RAG platforms, hybrid search, chunking, reranking |
| `04_agents_and_tooling` | Multi-agent, workflows, HITL, MCP, memory |
| `05_evaluation_and_observability` | LLM eval, A/B testing, hallucination, cost, safety |
| `06_platform_architecture` | LLM gateway, config-driven platform, vector DB, feature store |
| `07_recommendation_systems` | Video recs, feed ranking, two-tower, bandits |
| `08_case_studies_end_to_end` | Chatbot, research assistant, summarization, code assistant |
| `templates` | Reusable templates, checklists, diagram guides |


## How to Approach a New ML System Design Question

- Clarify requirements: functional, non-functional, scale, latency, cost
- Estimate scale: QPS, data volume, token budgets, storage
- Define API surface and data flow first
- Draw HLD with clear component boundaries
- Go deep on 1-2 components the interviewer cares about
