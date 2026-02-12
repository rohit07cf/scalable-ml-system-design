# Agentic AI — Interview-Ready Learning Module

> **Goal:** Go from "I've heard of agents" to "I can design multi-agent systems at scale" — in under 30 minutes of focused reading.

---

## Who This Is For

- AI Engineer candidates
- LLM Systems Design interviews
- Agentic AI architecture discussions
- Anyone building production agent systems

---

## Module Map

```
agentic_ai_learning/
│
├── 00_what_is_agentic_ai/        ← Start here
│   └── README.md
│
├── 01_core_concepts/              ← Foundations
│   ├── reasoning_loops.md
│   ├── tool_usage.md
│   ├── memory_systems.md
│   ├── planning.md
│   └── autonomy_controls.md
│
├── 02_agent_frameworks/           ← Framework landscape
│   └── langgraph_vs_crewai_vs_llamaindex_vs_autogen.md
│
├── 03_agent_development_stack/    ← What you build with
│   ├── llm_layer.md
│   ├── tooling_layer.md
│   ├── knowledge_layer.md
│   └── execution_layer.md
│
├── 04_agent_patterns/             ← Design patterns
│   ├── react.md
│   ├── plan_and_execute.md
│   ├── planner_executor.md
│   ├── multi_agent_collaboration.md
│   ├── self_reflection.md
│   └── environment_aware_agents.md
│
├── 05_multi_agent_systems/        ← Scaling agents
│   ├── architectures.md
│   ├── supervisor_model.md
│   ├── swarm_intelligence.md
│   └── use_cases.md
│
├── 06_building_agentic_ai_step_by_step/  ← Production guide
│   ├── blueprint.md
│   ├── security_and_compliance.md
│   └── observability.md
│
└── 07_evaluating_agentic_systems/ ← Evaluation & metrics
    ├── metrics.md
    ├── ragas_and_eval_tools.md
    ├── hallucination_detection.md
    └── cost_latency_analysis.md
```

---

## How to Read This

| If you have... | Read... |
|---|---|
| **10 minutes** | `00_what_is_agentic_ai/` + TL;DR sections only |
| **30 minutes** | All modules, skip "Practical Example" sections |
| **1 hour** | Everything end-to-end |
| **Interview tomorrow** | `04_agent_patterns/` + `05_multi_agent_systems/` + `07_evaluating_agentic_systems/` |

---

## Legend

| Symbol | Meaning |
|---|---|
| **Bold** | Key interview phrase — use these words |
| ⚠️ | Common trap / mistake |
| 💡 | Key insight to remember |
| `code` | Technical term or tool name |

---

## Quick Reference: The Agentic AI Stack

```
┌─────────────────────────────────────────────────┐
│                  USER / GOAL                     │
├─────────────────────────────────────────────────┤
│              ORCHESTRATION LAYER                 │
│   (LangGraph / CrewAI / Custom Supervisor)       │
├──────────┬──────────┬──────────┬────────────────┤
│ REASONING│  MEMORY  │  TOOLS   │   PLANNING     │
│  Loop    │ Short/   │ APIs,    │  Task Decomp,  │
│ (ReAct)  │ Long-term│ Code,SQL │  Goal Trees    │
├──────────┴──────────┴──────────┴────────────────┤
│                  LLM LAYER                       │
│     (GPT-4o / Claude / Gemini / Mistral)         │
├─────────────────────────────────────────────────┤
│              EXECUTION LAYER                     │
│   (K8s / Temporal / Serverless / Redis)          │
├─────────────────────────────────────────────────┤
│          OBSERVABILITY + SAFETY                  │
│   (LangSmith / Phoenix / Guardrails / RBAC)      │
└─────────────────────────────────────────────────┘
```

---

*Start with [00_what_is_agentic_ai/README.md](./00_what_is_agentic_ai/README.md) →*
