# Supervisor Model

## What It Is

- A **central coordinator agent** that routes tasks, manages workers, and synthesizes results
- The supervisor is the "brain" — it doesn't do the work, it decides WHO does WHAT
- Workers are specialized agents with specific tools and expertise
- Most common production pattern for multi-agent systems

## Why It Matters (Interview Framing)

> "The supervisor model is the go-to architecture for enterprise agent systems. When an interviewer says 'design a multi-agent system,' start with a supervisor. It's the safest, most debuggable, most controllable pattern."

---

## Simple Mental Model

> **Supervisor** = Air Traffic Controller
> - Doesn't fly planes (doesn't execute tasks)
> - Tells each plane where to go (routes tasks to agents)
> - Monitors all planes (tracks all agent states)
> - Handles conflicts and emergencies (error handling)

---

## Architecture

```
                 User Request
                      │
                      ▼
              ┌──────────────┐
              │  SUPERVISOR   │
              │               │
              │ 1. Understand │
              │    request    │
              │ 2. Decide     │
              │    which agent│
              │ 3. Monitor    │
              │    progress   │
              │ 4. Aggregate  │
              │    results    │
              └──────┬───────┘
           ┌─────────┼──────────┐
           ▼         ▼          ▼
     ┌──────────┐┌──────────┐┌──────────┐
     │ Worker A ││ Worker B ││ Worker C │
     │(Researcher││(Analyst) ││(Writer)  │
     │          ││          ││          │
     │ search() ││ python() ││ format() │
     │ scrape() ││ sql()    ││ pdf()    │
     └──────────┘└──────────┘└──────────┘
```

---

## Supervisor Decision Logic

```python
SUPERVISOR_PROMPT = """
You are a supervisor managing a team of agents.

Available agents:
- researcher: Searches web, reads documents, gathers information
- analyst: Runs Python code, SQL queries, creates charts
- writer: Generates reports, summaries, presentations

Given the current state and user request, decide:
1. Which agent should work next?
2. What specific task should they perform?
3. Is the overall goal complete?

Respond with:
- next_agent: <agent_name> OR "FINISH"
- task: <specific instruction for the agent>
- reasoning: <why this agent/task>
"""
```

---

## Implementation (LangGraph Style)

```python
from langgraph.graph import StateGraph, END

def supervisor_node(state):
    """Supervisor decides next action"""
    messages = state["messages"]
    response = supervisor_llm.invoke(
        SUPERVISOR_PROMPT + f"\nConversation: {messages}"
    )

    if response.next_agent == "FINISH":
        return {"next": END}

    return {
        "next": response.next_agent,
        "task": response.task
    }

def researcher_node(state):
    """Research agent executes task"""
    result = researcher_agent.run(state["task"])
    return {"messages": state["messages"] + [result]}

def analyst_node(state):
    """Analysis agent executes task"""
    result = analyst_agent.run(state["task"])
    return {"messages": state["messages"] + [result]}

# Build graph
graph = StateGraph()
graph.add_node("supervisor", supervisor_node)
graph.add_node("researcher", researcher_node)
graph.add_node("analyst", analyst_node)
graph.add_node("writer", writer_node)

# Supervisor routes to workers
graph.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],
    {
        "researcher": "researcher",
        "analyst": "analyst",
        "writer": "writer",
        END: END
    }
)

# Workers always return to supervisor
graph.add_edge("researcher", "supervisor")
graph.add_edge("analyst", "supervisor")
graph.add_edge("writer", "supervisor")

graph.set_entry_point("supervisor")
```

---

## Supervisor Execution Flow

```
User: "Analyze our Q4 sales and create a report"

Supervisor: → Route to researcher
  "Search for Q4 sales data in our internal database"

Researcher: → Executes
  "Found: Q4 revenue $12.3M, 15% YoY growth, 3 regions..."

Supervisor: → Route to analyst
  "Create charts for revenue by region and YoY comparison"

Analyst: → Executes
  "Generated: bar_chart.png, line_chart.png, summary_stats.json"

Supervisor: → Route to writer
  "Write executive summary using research data and charts"

Writer: → Executes
  "Executive Summary: Q4 showed strong growth..."

Supervisor: → FINISH
  Return compiled report to user
```

---

## Supervisor Design Patterns

| Pattern | Description |
|---|---|
| **Round-robin** | Supervisor cycles through agents in order |
| **Dynamic routing** | LLM decides which agent based on context |
| **Parallel dispatch** | Send independent tasks to multiple agents simultaneously |
| **Escalation** | Supervisor tries cheap agent first, escalates to expensive one |
| **Voting** | Send same task to multiple agents, supervisor picks best result |

---

## Practical Example: Customer Support Supervisor

```
┌────────────────────────────────────────┐
│         SUPPORT SUPERVISOR              │
│                                        │
│  Routes based on:                      │
│  - Ticket category                     │
│  - Customer tier                       │
│  - Complexity                          │
└────────────────────┬───────────────────┘
           ┌─────────┼──────────┐
           ▼         ▼          ▼
     ┌──────────┐┌──────────┐┌──────────┐
     │ FAQ      ││ Account  ││ Technical│
     │ Agent    ││ Agent    ││ Agent    │
     │          ││          ││          │
     │ Handles: ││ Handles: ││ Handles: │
     │ -general ││ -billing ││ -bugs    │
     │  questions││ -upgrades││ -config  │
     │ -policies││ -refunds ││ -integr. │
     │          ││          ││          │
     │ Escalates││ Escalates││ Escalates│
     │ to human ││ if >$500 ││ if P0    │
     └──────────┘└──────────┘└──────────┘
```

---

## Interview Questions They Will Ask

1. **"How does the supervisor decide which agent to call?"**
   → LLM-based routing: supervisor LLM receives the current state and available agents, uses reasoning to pick the best agent for the next step. Can also use rule-based routing for common patterns.

2. **"What if the supervisor makes a wrong routing decision?"**
   → Agent reports back inability or poor results. Supervisor re-evaluates and routes to a different agent. Max re-routing limit prevents infinite loops.

3. **"Can the supervisor be a bottleneck?"**
   → Yes, it's the single coordination point. Mitigations: make supervisor calls lightweight (cheap model), allow parallel dispatch, use rule-based pre-routing for common patterns.

4. **"How is this different from a microservices API gateway?"**
   → API gateway routes by URL/header (static). Supervisor routes by reasoning about task content (dynamic). The supervisor understands WHAT needs to be done, not just WHERE to send it.

5. **"How do you implement this in LangGraph?"**
   → Supervisor as a node with conditional edges to worker nodes. Workers always edge back to supervisor. Supervisor returns END when goal is complete.

---

## Common Mistakes

⚠️ **Supervisor that does everything** — The supervisor should route, not execute. If it starts doing work itself, you've collapsed back to a single agent.

⚠️ **No max routing loops** — Supervisor can bounce between agents indefinitely. Set a max loop count (10-15 typically).

⚠️ **Expensive supervisor model** — The supervisor makes routing decisions, not complex reasoning. Use a cheaper, faster model.

⚠️ **Workers with overlapping capabilities** — Clear role boundaries prevent confusion. If two agents can both search, the supervisor won't know which to choose.

⚠️ **No state passing between agents** — Workers need to see what previous agents produced. Pass accumulated context through shared state.

---

## TL;DR

- Supervisor = **central coordinator** that routes tasks to specialist worker agents
- Workers **always report back** to the supervisor
- Supervisor decides: **which agent, what task, when to finish**
- Most **common and production-ready** multi-agent architecture
- Use **cheap model for supervisor**, specialized models for workers
