#!/usr/bin/env python3
"""
End-to-end demo of the hierarchical agent tree.

Showcases all features ported from the reference configurable_agent:
  - AgentTree construction with Supervisor + 3 child agents
  - Tool execution via registered async callables (reference: @function_tool)
  - Agents-as-tools pattern (reference: agent.as_tool())
  - Structured HandoffResult for every child→Supervisor communication
  - Plan-then-execute pipeline (reference: call_reasoner → Runner.run)
  - Three-tier hooks: agent + tool + reasoning (reference: MyAgentHooks + MyRunHooks)
  - Context enrichment between steps (needs_more_info → enrich → next child)

Run:
    python -m agent_tree.demo          (from design_agentic_ai_platform/)
    python agent_tree/demo.py          (also works)

No external dependencies beyond Pydantic (pip install pydantic).
"""

from __future__ import annotations

import asyncio
import sys
import os
import time

# ── Path fixup so the script works both as `python agent_tree/demo.py`
#    and `python -m agent_tree.demo` ────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_tree.agent_node import AgentNode
from agent_tree.agent_tree import AgentTree
from agent_tree.handoff_models import HandoffResult, HandoffTraces, ToolResult
from agent_tree.orchestrator import OrchestratorHooks, SupervisorOrchestrator


# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS  (mirrors reference's tools.py @function_tool pattern)
# ═══════════════════════════════════════════════════════════════════════════
# These are real async callables — not canned results.  Each returns typed
# data that the agent wraps into a HandoffResult.

async def classify_intent(text: str) -> str:
    """Heuristic keyword-based intent classifier (reference: tools.py)."""
    lower = text.lower()
    if any(w in lower for w in ["invoice", "bill", "payment", "po"]):
        return "invoice_dispute"
    if any(w in lower for w in ["refund", "return", "credit"]):
        return "refund_request"
    return "general_query"


async def erp_lookup(invoice_id: str) -> dict:
    """Simulates an ERP system lookup (reference: tools.py add_numbers-style)."""
    # In production: async HTTP call to ERP API
    db = {
        "4821": {"status": "rejected", "reason": "missing_po", "amount_cents": 15000},
        "5012": {"status": "approved", "reason": None, "amount_cents": 32000},
    }
    return db.get(invoice_id, {"status": "not_found", "reason": None, "amount_cents": 0})


async def policy_search(query: str) -> str:
    """Simulates a policy database search."""
    return "Policy 7.3: All invoices above $100 require a valid PO number."


async def verify_answer(answer: str, sources: str) -> dict:
    """Simulates cross-checking an answer against policy."""
    return {"verified": True, "confidence": 0.95, "policy_ref": "7.3"}


# ═══════════════════════════════════════════════════════════════════════════
# CHILD AGENT CALLABLES  (each uses tools internally + returns HandoffResult)
# ═══════════════════════════════════════════════════════════════════════════
# These mirror the reference's BaseAgent subclasses from tree.py, but as
# simple async functions that use node.run_tool() for tool execution.

async def triage_agent_fn(user_input: str) -> HandoffResult:
    """Triage: classifies the request, returns needs_more_info for routing."""
    # Simulate a reasoning step (reference: reasoning_step tool)
    thought = "User is asking about an invoice rejection — classify intent first."

    # Run the classify tool directly (in production, the agent node would
    # call node.run_tool via the orchestrator's tool hooks)
    intent = await classify_intent(text=user_input)

    return HandoffResult(
        from_agent="triage",
        to_agent="supervisor",
        status="needs_more_info",
        summary=f"Classified as '{intent}' — routing to specialist.",
        payload={"intent": intent, "confidence": 0.88},
        traces=HandoffTraces(
            step_id="step_001",
            tool_calls=["classify_intent"],
            reasoning_steps=[thought],
            token_usage=1200,
        ),
    )


async def invoice_specialist_fn(user_input: str) -> HandoffResult:
    """Specialist: looks up invoice details + policy, returns structured answer."""
    # Reasoning step
    thought = "Need to look up invoice in ERP and check against policy."

    # Tool calls — real async execution
    erp_result = await erp_lookup(invoice_id="4821")
    policy_result = await policy_search(query="invoice rejection PO")

    # Build answer from tool results
    reason = erp_result.get("reason", "unknown")
    answer = f"Invoice #4821 was rejected: {reason}. {policy_result}"

    return HandoffResult(
        from_agent="invoice-specialist",
        to_agent="supervisor",
        status="ok",
        summary="Invoice #4821 rejected due to missing PO number.",
        payload={
            "invoice_id": "4821",
            "erp_data": erp_result,
            "policy": policy_result,
            "answer": answer,
        },
        artifacts=["erp://invoices/4821"],
        traces=HandoffTraces(
            step_id="step_002",
            tool_calls=["erp_lookup", "policy_search"],
            tool_results=[
                ToolResult(tool_name="erp_lookup", input_args={"invoice_id": "4821"}, output=erp_result, status="ok"),
                ToolResult(tool_name="policy_search", input_args={"query": "invoice rejection PO"}, output=policy_result, status="ok"),
            ],
            reasoning_steps=[thought],
            token_usage=2500,
            latency_ms=450,
        ),
    )


async def verifier_agent_fn(user_input: str) -> HandoffResult:
    """Verifier: cross-checks the answer against policy DB."""
    thought = "Cross-checking answer against policy database for accuracy."

    verification = await verify_answer(
        answer="Invoice #4821 rejected due to missing PO number.",
        sources="erp_lookup, policy_search",
    )

    return HandoffResult(
        from_agent="verifier",
        to_agent="supervisor",
        status="ok",
        summary="Answer verified against policy DB — correct.",
        payload={"verification": verification},
        traces=HandoffTraces(
            step_id="step_003",
            tool_calls=["verify_answer"],
            reasoning_steps=[thought],
            token_usage=800,
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════
# PLANNER  (mirrors reference's call_reasoner / reasoning_prompt.py)
# ═══════════════════════════════════════════════════════════════════════════

async def simple_planner(user_input: str) -> dict:
    """Produce a structured plan from user input.

    In production: an LLM call using the reference's REASONING_TEMPLATE.
    Here: keyword-based heuristic for demo purposes.
    """
    lower = user_input.lower()
    if "invoice" in lower:
        return {
            "strategy": "triage → invoice-specialist → verifier",
            "step_1": "Classify intent via triage agent",
            "step_2": "Look up invoice details via specialist",
            "step_3": "Verify answer via verifier agent",
        }
    return {
        "strategy": "triage → general handler",
        "step_1": "Classify intent via triage agent",
        "step_2": "Route to appropriate specialist",
    }


# ═══════════════════════════════════════════════════════════════════════════
# HOOK IMPLEMENTATIONS  (three-tier: agent + tool + reasoning)
# ═══════════════════════════════════════════════════════════════════════════

async def on_node_start(node: AgentNode, user_input: str) -> None:
    print(f"  [hook] node_start       → {node.name}")


async def on_node_end(node: AgentNode, result: HandoffResult) -> None:
    print(f"  [hook] node_end         → {node.name}  status={result.status}")


async def on_handoff(result: HandoffResult) -> None:
    print(f"  [hook] handoff          → {result.from_agent} ──▶ {result.to_agent}  |  {result.summary}")


async def on_tool_start(tool_name: str, args: dict) -> None:
    print(f"  [hook] tool_start       → {tool_name}({args})")


async def on_tool_end(tool_name: str, result: ToolResult) -> None:
    print(f"  [hook] tool_end         → {tool_name}  status={result.status}")


async def on_reasoning_step(agent_name: str, thought: str) -> None:
    print(f"  [hook] reasoning_step   → [{agent_name}] {thought}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN DEMO
# ═══════════════════════════════════════════════════════════════════════════

async def main() -> None:
    # ── 1) Build the agent tree ───────────────────────────────────────
    supervisor = AgentNode("supervisor", metadata={"role": "orchestrator"})

    # Child nodes with real tool callables registered
    triage = AgentNode("triage", agent=triage_agent_fn)
    triage.add_tool(classify_intent)  # register as callable (not just a string)

    invoice = AgentNode("invoice-specialist", agent=invoice_specialist_fn)
    invoice.add_tool(erp_lookup)
    invoice.add_tool(policy_search)

    verifier = AgentNode("verifier", agent=verifier_agent_fn)
    verifier.add_tool(verify_answer)

    supervisor.add_child(triage)
    supervisor.add_child(invoice)
    supervisor.add_child(verifier)

    # Demonstrate agents-as-tools: the supervisor can also call children as tools
    # (mirrors reference's sdk_agents.py: child_agent.as_tool())
    supervisor.add_tool(invoice.as_tool("run_invoice_specialist"))
    supervisor.add_tool(verifier.as_tool("run_verifier"))

    tree = AgentTree(supervisor)

    # ── 2) Print the tree ─────────────────────────────────────────────
    print("=" * 64)
    print("AGENT TREE")
    print("=" * 64)
    print(tree.visualize())
    print()

    # ── 3) Demonstrate AgentNode.run_tool() directly ──────────────────
    print("=" * 64)
    print("DIRECT TOOL EXECUTION (AgentNode.run_tool)")
    print("=" * 64)
    tool_result = await invoice.run_tool("erp_lookup", invoice_id="4821")
    print(f"  erp_lookup('4821') → {tool_result.output}  ({tool_result.latency_ms}ms)")
    tool_result2 = await invoice.run_tool("policy_search", query="PO requirement")
    print(f"  policy_search(...)  → {tool_result2.output}")
    print()

    # ── 4) Run the full orchestrator with planner + hooks ─────────────
    hooks = OrchestratorHooks(
        on_node_start=on_node_start,
        on_node_end=on_node_end,
        on_handoff=on_handoff,
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
        on_reasoning_step=on_reasoning_step,
    )
    orchestrator = SupervisorOrchestrator(
        tree=tree,
        hooks=hooks,
        max_steps=10,
        planner=simple_planner,  # plan-then-execute (reference: call_reasoner)
    )

    print("=" * 64)
    print("ORCHESTRATION RUN (plan-then-execute)")
    print("=" * 64)
    prompt = "Why was invoice #4821 rejected?"
    print(f"  User prompt: {prompt!r}\n")

    start = time.perf_counter()
    result = await orchestrator.run(prompt)
    elapsed = time.perf_counter() - start

    # ── 5) Print the plan ─────────────────────────────────────────────
    print()
    print("=" * 64)
    print("PLANNER OUTPUT")
    print("=" * 64)
    if result.plan:
        for k, v in result.plan.items():
            print(f"  {k}: {v}")
    print()

    # ── 6) Print handoff summaries ────────────────────────────────────
    print("=" * 64)
    print("HANDOFF SUMMARIES")
    print("=" * 64)
    for i, h in enumerate(result.handoffs_received, 1):
        print(f"  [{i}] {h.from_agent} → {h.to_agent}")
        print(f"      status:     {h.status}")
        print(f"      summary:    {h.summary}")
        print(f"      tokens:     {h.traces.token_usage}")
        if h.traces.tool_calls:
            print(f"      tool_calls: {h.traces.tool_calls}")
        if h.traces.tool_results:
            for tr in h.traces.tool_results:
                print(f"        └─ {tr.tool_name}: {tr.output} ({tr.latency_ms}ms)")
        if h.traces.reasoning_steps:
            for rs in h.traces.reasoning_steps:
                print(f"      reasoning:  \"{rs}\"")
        if h.artifacts:
            print(f"      artifacts:  {h.artifacts}")
        print()

    # ── 7) Print final output ─────────────────────────────────────────
    print("=" * 64)
    print("SUPERVISOR FINAL OUTPUT")
    print("=" * 64)
    print(f"  Status:       {result.status}")
    print(f"  Answer:       {result.answer}")
    print(f"  Total steps:  {result.total_steps}")
    print(f"  Total tokens: {result.total_tokens}")
    print(f"  Wall time:    {elapsed:.3f}s")
    print()


if __name__ == "__main__":
    asyncio.run(main())
