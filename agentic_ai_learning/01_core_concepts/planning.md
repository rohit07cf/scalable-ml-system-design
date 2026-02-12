# Planning

## What It Is

- **Planning** = the agent's ability to decompose a high-level goal into an ordered sequence of subtasks
- It's the "thinking before doing" phase — what separates smart agents from brute-force ones
- Planning can be static (upfront) or dynamic (re-plan as you go)
- Closely tied to task decomposition, dependency management, and goal tracking

## Why It Matters (Interview Framing)

> "Interviewers love planning questions because they test system-level thinking. Anyone can call an LLM — designing how an agent breaks down 'build me a dashboard' into 20 ordered steps with dependencies is the real challenge."

---

## Simple Mental Model

> Planning is like a **project manager** inside the agent:
> - Receives a vague goal ("build a report")
> - Breaks it into tasks ("gather data", "analyze", "format", "review")
> - Orders them (can't analyze before gathering)
> - Tracks progress and adjusts the plan if things go wrong

---

## Planning Approaches

### 1. Hierarchical Planning

```
Goal: "Create quarterly financial report"
│
├─ Phase 1: Data Collection
│   ├─ Task 1.1: Fetch revenue data from API
│   ├─ Task 1.2: Fetch expense data from DB
│   └─ Task 1.3: Fetch market benchmarks
│
├─ Phase 2: Analysis
│   ├─ Task 2.1: Calculate YoY growth
│   ├─ Task 2.2: Expense breakdown by category
│   └─ Task 2.3: Compare to benchmarks
│
├─ Phase 3: Report Generation
│   ├─ Task 3.1: Generate charts
│   ├─ Task 3.2: Write executive summary
│   └─ Task 3.3: Compile final PDF
│
└─ Phase 4: Review
    └─ Task 4.1: Self-check for accuracy
```

- **How:** Break goal into phases → break phases into tasks
- **When:** Complex, multi-phase workflows
- **Strength:** Clear structure, easy to track progress
- **Weakness:** Upfront planning may not survive contact with reality

---

### 2. Task Decomposition

```
Input:  "Summarize the top 5 papers on RAG published this year"

Decomposed:
  1. Search for RAG papers published 2025
  2. Rank by citation count / relevance
  3. Select top 5
  4. For each paper:
     a. Fetch abstract and key findings
     b. Write 3-sentence summary
  5. Compile into final summary document
```

- **How:** LLM breaks a task into atomic, executable steps
- **When:** Any task that isn't trivially single-step
- **Key prompt pattern:** "Break this goal into a numbered list of steps"

💡 **Task decomposition is the most commonly used planning technique in practice.**

---

### 3. Multi-Step Workflows

```
┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
│Step 1│───▶│Step 2│───▶│Step 3│───▶│Step 4│
│Fetch │    │Parse │    │Analyze│   │Report│
└──────┘    └──────┘    └──────┘    └──────┘
                │
                ├── if error → Retry Step 1
                └── if missing data → Insert Step 1.5
```

- **How:** Linear or DAG-based execution of ordered steps
- **When:** Predictable workflows with clear inputs/outputs
- **Tools:** LangGraph, Temporal, Airflow, Prefect

---

### 4. Goal-Oriented Planning

```
Current State:  No report exists
Goal State:     Accurate quarterly report in user's inbox

Planner generates:
  actions = [
    fetch_data(),
    validate_data(),       ← Added because data might be incomplete
    run_analysis(),
    generate_report(),
    quality_check(),       ← Added because report must be accurate
    email_report()
  ]
```

- **How:** Define current state + goal state, planner fills in the action sequence
- **When:** Open-ended tasks where the path isn't obvious
- **Inspired by:** Classical AI planning (STRIPS, PDDL)

---

## Static vs Dynamic Planning

| Aspect | Static Planning | Dynamic Planning |
|---|---|---|
| **When planned** | Before execution starts | Re-planned after each step |
| **Flexibility** | Low — fixed plan | High — adapts to results |
| **Cost** | Lower (plan once) | Higher (re-plan each step) |
| **Failure handling** | Poor — plan breaks | Good — re-plans around failure |
| **Best for** | Well-understood workflows | Uncertain, exploratory tasks |

💡 **Production systems often use a hybrid:** static high-level plan + dynamic step-level replanning.

---

## Architecture: Planning in an Agent

```
┌─────────────────────────────────────────┐
│                  AGENT                   │
│                                         │
│  ┌──────────┐    ┌───────────────────┐  │
│  │ PLANNER  │───▶│   TASK QUEUE      │  │
│  │ (LLM)    │    │  [T1, T2, T3...]  │  │
│  └──────────┘    └────────┬──────────┘  │
│       ▲                   │             │
│       │              ┌────▼─────┐       │
│       │              │ EXECUTOR │       │
│       │              │ (picks   │       │
│       │              │  next T) │       │
│       │              └────┬─────┘       │
│       │                   │             │
│       │              ┌────▼─────┐       │
│       └──── replan ──│ EVALUATOR│       │
│         if needed    │ (check   │       │
│                      │  result) │       │
│                      └──────────┘       │
└─────────────────────────────────────────┘
```

---

## Practical Example: Planning Prompt

```python
PLANNING_PROMPT = """
You are a planning agent. Given a user goal, create an execution plan.

Rules:
- Break into atomic, executable steps
- Each step should have: description, tool needed, dependencies
- Order by dependencies (no step runs before its deps)
- Mark which steps can run in parallel

User Goal: {goal}

Output format:
Step 1: [description] | Tool: [tool_name] | Deps: [] | Parallel: false
Step 2: [description] | Tool: [tool_name] | Deps: [1] | Parallel: false
Step 3: [description] | Tool: [tool_name] | Deps: [1] | Parallel: true (with Step 2)
...
"""
```

---

## Interview Questions They Will Ask

1. **"How does an agent decide what to do first?"**
   → Planning: decompose the goal, identify dependencies, order tasks. Use LLM-based task decomposition or predefined DAGs.

2. **"Static vs dynamic planning — trade-offs?"**
   → Static = cheaper, predictable, but fragile. Dynamic = adaptive, but more expensive and complex. Hybrid is usually best.

3. **"How do you handle plan failures?"**
   → Re-planning. If a step fails, feed the error to the planner and generate an updated plan. Always have a max-retry limit.

4. **"How would you plan a complex multi-step research task?"**
   → Hierarchical: goal → phases → tasks. Each task has clear inputs, outputs, tools, and success criteria.

5. **"Can agents do parallel execution?"**
   → Yes, if tasks have no dependencies. The planner must identify which tasks are independent. Execution layer runs them concurrently.

---

## Common Mistakes

⚠️ **No planning at all** — Jumping straight to execution works for simple tasks but fails spectacularly on complex ones.

⚠️ **Over-planning** — Spending 10 steps planning a 2-step task wastes tokens and time. Scale planning to task complexity.

⚠️ **Rigid plans** — Plans that can't adapt to failures or unexpected results will break in production.

⚠️ **Ignoring dependencies** — Running Step 3 before Step 1 completes = garbage output. Always model task dependencies.

⚠️ **Not validating plan quality** — LLMs sometimes generate plans with circular dependencies or impossible steps. Validate before executing.

---

## TL;DR

- **Planning** = decompose goals into ordered, executable subtasks
- Four approaches: **Hierarchical, Task Decomposition, Multi-Step, Goal-Oriented**
- **Static** plans are cheaper but fragile; **Dynamic** plans adapt but cost more
- Production systems use **hybrid** planning (static structure + dynamic replanning)
- Always model **dependencies** and allow for **plan failure + replanning**
