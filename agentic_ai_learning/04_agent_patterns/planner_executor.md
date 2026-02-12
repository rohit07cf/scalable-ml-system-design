# Planner-Executor Pattern

## What It Is

- **Planner-Executor** = two separate agents: one plans, one executes — each specialized
- Unlike Plan & Execute (single agent, two phases), this uses **two distinct agents** with different roles
- The Planner agent generates and manages the task plan
- The Executor agent carries out individual tasks, reporting back results
- Communication between them is explicit and structured

## Why It Matters (Interview Framing)

> "This pattern is the stepping stone to multi-agent systems. Interviewers use it to test if you understand agent specialization, inter-agent communication, and separation of concerns. It's also a practical architecture for production systems."

---

## Simple Mental Model

> **Planner** = Tech Lead who creates tickets and assigns work
> **Executor** = Developer who picks up tickets, does the work, reports results
> They communicate through a shared task board.

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│            PLANNER-EXECUTOR PATTERN                │
│                                                   │
│  ┌────────────────┐     ┌────────────────┐       │
│  │    PLANNER     │     │   EXECUTOR     │       │
│  │    AGENT       │     │   AGENT        │       │
│  │                │     │                │       │
│  │ - Strong LLM   │     │ - Fast LLM     │       │
│  │ - No tools     │     │ - Has tools    │       │
│  │ - Manages plan │     │ - Executes     │       │
│  │ - Evaluates    │     │ - Reports      │       │
│  └───────┬────────┘     └───────▲────────┘       │
│          │                      │                │
│          │   ┌──────────────┐   │                │
│          └──▶│  TASK QUEUE  │───┘                │
│              │              │                    │
│              │ Task 1: ✅   │                    │
│              │ Task 2: 🔄   │  ← Current        │
│              │ Task 3: ⏳   │                    │
│              │ Task 4: ⏳   │                    │
│              └──────────────┘                    │
└──────────────────────────────────────────────────┘
```

---

## How It Differs from Plan & Execute

| Aspect | Plan & Execute | Planner-Executor |
|---|---|---|
| **Agents** | One agent, two phases | Two separate agents |
| **Specialization** | Same LLM plans and executes | Planner = reasoning, Executor = doing |
| **Communication** | Internal (same context) | External (shared state / messages) |
| **LLM usage** | Can use different models per phase | Each agent has its own model |
| **Scalability** | Single thread | Executor can be parallelized |
| **Reusability** | Monolithic | Executor is reusable across tasks |

---

## Implementation

```python
class PlannerAgent:
    def __init__(self, llm="gpt-4o"):
        self.llm = llm

    def create_plan(self, goal):
        """Generate initial task plan"""
        return self.llm.call(
            f"Break this goal into tasks: {goal}\n"
            f"Output: JSON list of tasks with description and success criteria"
        )

    def evaluate_result(self, task, result):
        """Check if a task was completed successfully"""
        return self.llm.call(
            f"Task: {task.description}\n"
            f"Success criteria: {task.criteria}\n"
            f"Result: {result}\n"
            f"Was this task completed successfully? If not, what should be retried?"
        )

    def replan(self, original_plan, completed, failed_task, error):
        """Generate updated plan after failure"""
        return self.llm.call(
            f"Original plan: {original_plan}\n"
            f"Completed: {completed}\n"
            f"Failed: {failed_task} with error: {error}\n"
            f"Generate updated remaining plan."
        )


class ExecutorAgent:
    def __init__(self, llm="gpt-4o-mini", tools=None):
        self.llm = llm
        self.tools = tools

    def execute_task(self, task):
        """Execute a single task using ReAct loop"""
        return react_loop(
            goal=task.description,
            tools=self.tools,
            llm=self.llm,
            max_iterations=5
        )


# Orchestration
def planner_executor(goal, tools):
    planner = PlannerAgent(llm="gpt-4o")
    executor = ExecutorAgent(llm="gpt-4o-mini", tools=tools)

    plan = planner.create_plan(goal)

    for task in plan.tasks:
        result = executor.execute_task(task)
        evaluation = planner.evaluate_result(task, result)

        if evaluation.success:
            task.mark_complete(result)
        else:
            updated_plan = planner.replan(plan, completed, task, result.error)
            plan = updated_plan

    return compile_results(plan)
```

---

## When to Use

| Scenario | Planner-Executor? |
|---|---|
| Tasks needing strong planning + cheap execution | **Yes** |
| Multiple executors working in parallel | **Yes** |
| Reusable executor across different planners | **Yes** |
| Simple single-step tasks | **No** — overkill |
| Tasks where planning and execution are tightly coupled | **No** — use Plan & Execute |

---

## Practical Example: Code Refactoring Agent

```
PLANNER receives: "Refactor the authentication module to use JWT"

PLANNER creates plan:
  Task 1: Analyze current auth module structure
  Task 2: Identify all auth-related endpoints
  Task 3: Design JWT token schema
  Task 4: Implement JWT generation and validation
  Task 5: Update endpoints to use JWT
  Task 6: Update tests
  Task 7: Run test suite

EXECUTOR executes Task 1:
  → Uses code_search tool to find auth module
  → Uses read_file tool to analyze structure
  → Returns: "Auth module uses session-based auth with 5 endpoints"

PLANNER evaluates: ✅ Task 1 complete
PLANNER sends Task 2 to EXECUTOR...

[continues through all tasks]

EXECUTOR executes Task 6:
  → Tests fail: 3 endpoints returning 401

PLANNER re-evaluates: ❌ Task 5 incomplete
PLANNER replans: Add Task 5b: "Fix token header format for 3 failing endpoints"
```

---

## Interview Questions They Will Ask

1. **"How is Planner-Executor different from Plan & Execute?"**
   → Planner-Executor uses two separate, specialized agents. Plan & Execute is one agent with two phases. P-E has better separation of concerns and allows parallel execution.

2. **"Why use two agents instead of one?"**
   → Specialization: planner can use a strong (expensive) model for reasoning, executor can use a cheaper model for tool calls. Also enables parallel execution and reusable executors.

3. **"How do the planner and executor communicate?"**
   → Through a shared task queue or message bus. Planner writes tasks, executor picks them up, reports results. Planner evaluates results and updates the plan.

4. **"Can you have multiple executors?"**
   → Yes. Independent tasks can be dispatched to multiple executor agents in parallel. This is the bridge to full multi-agent systems.

5. **"What happens when the executor fails?"**
   → Executor reports the failure. Planner evaluates whether to retry, modify the task, or replan the remaining work.

---

## Common Mistakes

⚠️ **Using the same model for both** — The whole point is specialization. Use a strong planner, cheap executor.

⚠️ **Tight coupling** — Planner and executor should communicate via structured messages, not shared context. This enables independent scaling and replacement.

⚠️ **No evaluation step** — The planner must verify the executor's results. Without evaluation, errors cascade through the plan.

⚠️ **Over-detailed plans** — The planner should give the executor enough direction but not micromanage. Let the executor use its tools flexibly.

⚠️ **Confusing with Plan & Execute** — These are different patterns. Know the distinction for interviews.

---

## TL;DR

- **Two specialized agents:** Planner (reasoning) + Executor (action)
- Planner uses strong model, Executor uses cheaper model → **cost efficient**
- Communication via **shared task queue / structured messages**
- Enables **parallel execution** and **reusable executors**
- Bridge pattern between single-agent and **full multi-agent systems**
