# ReAct Pattern (Reasoning + Acting)

## What It Is

- **ReAct** = Interleave **Reasoning** (Thought) with **Acting** (Tool calls) in a loop
- The most widely used agent pattern — it's the "default" for general-purpose agents
- Each iteration: the LLM reasons about what to do next, calls a tool, observes the result, and reasons again
- Paper: "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)

## Why It Matters (Interview Framing)

> "ReAct is the foundational agent pattern. If you only learn one pattern, learn this one. Every framework (LangChain, LlamaIndex, OpenAI) implements it. Interviewers will expect you to explain it, implement it, and know its limitations."

---

## Simple Mental Model

> ReAct is like **thinking out loud while doing work:**
> "I need to find X... let me search... I found Y... that's not quite right... let me refine..."

---

## The ReAct Loop

```
┌──────────────────────────────────────────┐
│              ReAct LOOP                   │
│                                          │
│  ┌──────────┐                            │
│  │ THOUGHT  │  "I need to find the       │
│  │          │   user's order status"      │
│  └────┬─────┘                            │
│       │                                  │
│  ┌────▼─────┐                            │
│  │  ACTION  │  call: get_order("ORD-123")│
│  │          │                            │
│  └────┬─────┘                            │
│       │                                  │
│  ┌────▼──────────┐                       │
│  │ OBSERVATION   │  {status: "shipped",  │
│  │               │   eta: "March 15"}    │
│  └────┬──────────┘                       │
│       │                                  │
│  ┌────▼─────┐                            │
│  │ THOUGHT  │  "I have the info. The     │
│  │          │   order is shipped."        │
│  └────┬─────┘                            │
│       │                                  │
│  ┌────▼─────┐                            │
│  │  ACTION  │  respond("Your order       │
│  │ (final)  │   shipped, arriving 3/15") │
│  └──────────┘                            │
└──────────────────────────────────────────┘
```

---

## Implementation

```python
def react_agent(goal, tools, llm, max_iterations=10):
    context = [{"role": "system", "content": REACT_SYSTEM_PROMPT}]
    context.append({"role": "user", "content": goal})

    for i in range(max_iterations):
        # LLM generates Thought + Action
        response = llm.call(context)

        if response.is_final_answer:
            return response.answer

        # Parse the action
        tool_name, tool_args = response.parse_action()

        # Execute the tool
        observation = tools[tool_name].execute(**tool_args)

        # Append to context
        context.append({"role": "assistant", "content": response.text})
        context.append({"role": "tool", "content": str(observation)})

    return "Max iterations reached — could not complete task"
```

---

## ReAct System Prompt (Simplified)

```
You are a helpful assistant with access to tools.

For each step:
1. Thought: Reason about what to do next
2. Action: Call a tool with the right arguments
3. Observation: Read the tool result

Repeat until you can provide a final answer.

Available tools:
- search_web(query) - Search the internet
- get_order(order_id) - Look up an order
- run_code(python_code) - Execute Python code

When you have enough info, respond with:
Final Answer: [your response]
```

---

## When to Use ReAct

| Scenario | Use ReAct? |
|---|---|
| General Q&A with tool access | **Yes** — this is the sweet spot |
| Customer support with KB + APIs | **Yes** |
| Simple text generation | **No** — just call the LLM directly |
| Complex multi-phase projects | **Partially** — use Plan-and-Execute, with ReAct for each phase |
| Tasks requiring exploration of multiple paths | **No** — use Tree-of-Thought |

---

## Trade-offs

| Advantage | Disadvantage |
|---|---|
| Simple to implement | Sequential — can't explore multiple paths |
| Grounded in tool observations | Expensive for long chains (many LLM calls) |
| Easy to debug (trace Thought → Action → Observation) | Can get stuck in loops |
| Works with any LLM that supports tool use | Context window fills up with history |
| Well-supported by all frameworks | No upfront planning — may take suboptimal paths |

---

## Failure Modes

| Failure | Cause | Mitigation |
|---|---|---|
| **Infinite loop** | Agent repeats same action | Max iteration limit, loop detection |
| **Wrong tool selection** | Vague tool descriptions | Better tool descriptions, fewer tools |
| **Context overflow** | Too many steps | Summarize old steps, sliding window |
| **Hallucinated actions** | LLM invents tool names | Strict tool name validation |
| **Stuck state** | No progress being made | Progress detection, escalation |

---

## Interview Questions They Will Ask

1. **"Explain the ReAct pattern."**
   → Interleaved Thought-Action-Observation loop. Agent reasons about what to do, calls a tool, reads the result, reasons again. Repeats until goal is met.

2. **"What's the difference between ReAct and Chain-of-Thought?"**
   → CoT is reasoning-only (no tools). ReAct adds actions (tool calls) interleaved with reasoning. ReAct is grounded in real data; CoT relies solely on the LLM's knowledge.

3. **"How do you prevent a ReAct agent from looping forever?"**
   → Max iteration limit, token budget, loop detection (same action repeated), progress monitoring, timeout.

4. **"What are the limitations of ReAct?"**
   → Sequential (no parallel exploration), context window fills up, no upfront planning (may take suboptimal paths), expensive for long chains.

5. **"When would you choose something other than ReAct?"**
   → Complex multi-phase tasks → Plan-and-Execute. Multiple solution paths → Tree-of-Thought. Simple text generation → direct LLM call.

---

## Common Mistakes

⚠️ **No iteration limit** — ReAct loops can run forever. Always set `max_iterations`.

⚠️ **Too many tools** — More tools = more confusion for the LLM. Keep it under 10-15 per agent.

⚠️ **Not validating tool calls** — The LLM can hallucinate tool names or malform arguments. Validate before executing.

⚠️ **Ignoring context window** — Each step adds to the prompt. After 10+ steps, summarize earlier steps.

⚠️ **Using ReAct for everything** — Simple tasks don't need a reasoning loop. A single LLM call is faster and cheaper.

---

## TL;DR

- **ReAct** = Thought → Action → Observation → repeat
- The **default agent pattern** — use it unless you have a reason not to
- **Grounded** in real tool observations (not just LLM imagination)
- Limitations: **sequential, expensive for long chains, no upfront planning**
- Always set **max iterations and token budgets**
