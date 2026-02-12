# Plan & Execute Pattern

## What It Is

- **Plan & Execute** = first create a plan (list of steps), then execute each step sequentially
- Separates **planning** from **execution** — two distinct phases
- The planner is typically a stronger model; the executor can be cheaper
- Also known as "Plan & Solve" in some literature

## Why It Matters (Interview Framing)

> "Plan & Execute is the answer when interviewers ask 'How would you handle a complex, multi-step task?' It shows you understand that rushing into execution without a plan leads to wasted tokens and suboptimal paths."

---

## Simple Mental Model

> Plan & Execute is like a **project manager + developer team:**
> - The PM (planner) creates the task list
> - The devs (executors) work through each task
> - The PM reviews progress and adjusts the plan if needed

---

## Architecture

```
┌──────────────────────────────────────────────┐
│            PLAN & EXECUTE PATTERN             │
│                                              │
│  ┌──────────┐      ┌──────────────────────┐  │
│  │ PLANNER  │─────▶│      PLAN            │  │
│  │ (LLM)    │      │ 1. Fetch data        │  │
│  └──────────┘      │ 2. Analyze trends    │  │
│       ▲            │ 3. Create charts     │  │
│       │            │ 4. Write summary     │  │
│       │            │ 5. Review output     │  │
│    replan          └──────────┬───────────┘  │
│   if needed                   │              │
│       │            ┌──────────▼───────────┐  │
│       │            │     EXECUTOR          │  │
│       │            │  (executes each step  │  │
│       │            │   using ReAct or      │  │
│       └────────────│   direct tool calls)  │  │
│                    └──────────────────────┘  │
└──────────────────────────────────────────────┘
```

---

## How It Works

```
Phase 1: PLAN
  Input: "Analyze our competitor pricing and create a report"
  Output:
    Step 1: Search for competitor pricing data (tool: web_search)
    Step 2: Extract pricing from top 5 competitors (tool: web_scrape)
    Step 3: Organize into comparison table (tool: run_python)
    Step 4: Generate insights and recommendations (tool: llm_generate)
    Step 5: Format as PDF report (tool: create_pdf)

Phase 2: EXECUTE
  for each step in plan:
      result = executor.run(step)
      if result.failed:
          replan(step, error=result.error)

Phase 3: REPLAN (if needed)
  "Step 2 failed — website blocked scraping"
  Updated Step 2: Use cached pricing data from internal DB
```

---

## Implementation

```python
def plan_and_execute(goal, tools, planner_llm, executor_llm):
    # Phase 1: Plan
    plan = planner_llm.call(
        f"Create a step-by-step plan to: {goal}\n"
        f"Available tools: {tools.list_schemas()}\n"
        f"Output: numbered steps with tool assignments"
    )

    steps = parse_plan(plan)

    # Phase 2: Execute
    results = []
    for i, step in enumerate(steps):
        result = executor_llm.execute_step(
            step=step,
            context=results,  # Previous step results
            tools=tools
        )

        if result.success:
            results.append(result)
        else:
            # Phase 3: Replan
            updated_steps = planner_llm.replan(
                original_plan=steps,
                failed_step=i,
                error=result.error,
                completed=results
            )
            steps = updated_steps  # Continue with updated plan

    return compile_results(results)
```

---

## Plan & Execute vs ReAct

| Dimension | ReAct | Plan & Execute |
|---|---|---|
| **Planning** | None (decide each step on the fly) | Upfront plan before execution |
| **Efficiency** | May take suboptimal paths | More efficient — follows a plan |
| **Adaptability** | Highly adaptive (each step re-evaluated) | Less adaptive (plan may need updating) |
| **Cost** | Medium (sequential LLM calls) | Lower per-step (executor can use cheaper model) |
| **Complexity** | Simple | More complex (planner + executor + replanner) |
| **Best for** | Simple, single-objective tasks | Complex, multi-step tasks |
| **Failure mode** | Gets stuck, loops | Plan becomes invalid, needs replanning |

---

## When to Use

| Scenario | Use Plan & Execute? |
|---|---|
| Complex research task with 5+ steps | **Yes** |
| Simple Q&A with one tool call | **No** — overkill |
| Task with known dependencies between steps | **Yes** |
| Open-ended exploration | **No** — ReAct is more flexible |
| Tasks where you want to show the plan to the user | **Yes** — plan provides transparency |

---

## Practical Example: Market Research Agent

```
User Goal: "Create a competitive analysis report for our SaaS product"

PLAN:
  1. Identify top 5 competitors via web search
  2. For each competitor:
     a. Gather pricing data
     b. Gather feature list
     c. Gather customer reviews summary
  3. Create feature comparison matrix
  4. Analyze pricing strategy differences
  5. Identify our competitive advantages and gaps
  6. Write executive summary with recommendations
  7. Generate final PDF report

EXECUTE:
  Step 1: web_search("top competitors for [product category]")
  → Found: CompA, CompB, CompC, CompD, CompE

  Step 2a: web_scrape(CompA.pricing_page) → $29/$99/$249
  Step 2b: [continues for each competitor...]

  Step 3: run_python(create_comparison_matrix(data))
  → Generated: comparison_table.csv

  [Steps 4-7 continue...]

REPLAN TRIGGER:
  Step 2a failed for CompD (pricing page behind login)
  → Replan: "Use latest available pricing from review sites instead"
```

---

## Interview Questions They Will Ask

1. **"When would you use Plan & Execute over ReAct?"**
   → Complex multi-step tasks where upfront planning improves efficiency. When steps have dependencies. When you want to show the user a plan before execution.

2. **"How do you handle plan failures?"**
   → Replanning: feed the failed step and error back to the planner. It generates an updated plan that works around the failure. Set a max replan count.

3. **"Can you use different models for planning and execution?"**
   → Yes, and you should. Planner = strong model (GPT-4o) for reasoning. Executor = cheaper model (GPT-4o-mini) for straightforward tool calls. Saves cost.

4. **"What if the plan is wrong from the start?"**
   → Validate the plan before execution: check for circular dependencies, verify tool availability, sanity-check step count. Allow dynamic replanning.

5. **"How is Plan & Execute implemented in LangGraph?"**
   → Planner node generates a plan (list of tasks). Executor node processes each task. Conditional edge checks result — if failure, route back to planner for replanning.

---

## Common Mistakes

⚠️ **Plans that are too detailed** — Over-specified plans break when reality differs. Keep plans at the right abstraction level.

⚠️ **No replanning mechanism** — Plans will fail. If you can't replan, the agent is stuck.

⚠️ **Using Plan & Execute for simple tasks** — A 2-step task doesn't need a planner. Direct ReAct is simpler and faster.

⚠️ **Not validating the plan** — LLMs can generate plans with impossible steps, circular dependencies, or missing tool references. Validate before executing.

⚠️ **Plan drift** — As execution progresses, the plan may become irrelevant. Periodically re-evaluate whether the plan still makes sense.

---

## TL;DR

- **Plan & Execute** = create plan first, then execute step by step
- Best for **complex multi-step tasks** with dependencies
- Use **strong model for planning, cheaper model for execution**
- Always include **replanning** for when steps fail
- **Not needed for simple tasks** — use ReAct instead
