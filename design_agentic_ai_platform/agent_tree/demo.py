#!/usr/bin/env python3
"""
Minimal end-to-end demo of the hierarchical agent tree.

Builds a Supervisor with 3 child agents, runs a sample prompt, and
prints the tree visualisation, each handoff summary, and the final
Supervisor output.

Run:
    python -m agent_tree.demo          (from design_agentic_ai_platform/)
    python agent_tree/demo.py          (also works)

No external dependencies beyond Pydantic (pip install pydantic).
"""

from __future__ import annotations

import asyncio
import sys
import os

# ── Path fixup so the script works both as `python agent_tree/demo.py`
#    and `python -m agent_tree.demo` ────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_tree.agent_node import AgentNode
from agent_tree.agent_tree import AgentTree
from agent_tree.handoff_models import HandoffResult, HandoffTraces
from agent_tree.orchestrator import OrchestratorHooks, SupervisorOrchestrator


# ── Fake child agent callables ─────────────────────────────────────────
# In production these would call an LLM; here they return canned results
# wrapped in validated HandoffResult models.

async def triage_agent(user_input: str) -> HandoffResult:
    """Simulates a triage agent that classifies the request."""
    return HandoffResult(
        from_agent="triage",
        to_agent="supervisor",
        status="needs_more_info",
        summary="Classified as invoice dispute — needs specialist lookup.",
        payload={"category": "invoice_dispute", "confidence": 0.88},
        traces=HandoffTraces(step_id="step_001", tool_calls=["classify"], token_usage=1200),
    )


async def invoice_specialist(user_input: str) -> HandoffResult:
    """Simulates a specialist that looks up invoice details."""
    return HandoffResult(
        from_agent="invoice-specialist",
        to_agent="supervisor",
        status="ok",
        summary="Invoice #4821 rejected due to missing PO number.",
        payload={"invoice_id": "4821", "reason": "missing_po", "amount_cents": 15000},
        artifacts=["erp://invoices/4821"],
        traces=HandoffTraces(
            step_id="step_002",
            tool_calls=["erp_lookup", "policy_search"],
            token_usage=2500,
            latency_ms=450,
        ),
    )


async def verifier_agent(user_input: str) -> HandoffResult:
    """Simulates a verifier that cross-checks the answer."""
    return HandoffResult(
        from_agent="verifier",
        to_agent="supervisor",
        status="ok",
        summary="Answer verified against policy DB — correct.",
        payload={"verified": True},
        traces=HandoffTraces(step_id="step_003", tool_calls=["policy_check"], token_usage=800),
    )


# ── Hook implementations (just print to stdout) ───────────────────────

async def on_node_start(node: AgentNode, user_input: str) -> None:
    print(f"  [hook] node_start  → {node.name}")


async def on_node_end(node: AgentNode, result: HandoffResult) -> None:
    print(f"  [hook] node_end    → {node.name}  status={result.status}")


async def on_handoff(result: HandoffResult) -> None:
    print(f"  [hook] handoff     → {result.from_agent} ──▶ {result.to_agent}  |  {result.summary}")


# ── Main demo ──────────────────────────────────────────────────────────

async def main() -> None:
    # 1) Build the agent tree
    supervisor = AgentNode("supervisor", metadata={"role": "orchestrator"})

    triage = AgentNode("triage", tools=["classify"], agent=triage_agent)
    invoice = AgentNode("invoice-specialist", tools=["erp_lookup", "policy_search"], agent=invoice_specialist)
    verifier = AgentNode("verifier", tools=["policy_check"], agent=verifier_agent)

    # Triage is a child of Supervisor; specialists are children of Triage
    supervisor.add_child(triage)
    supervisor.add_child(invoice)
    supervisor.add_child(verifier)

    tree = AgentTree(supervisor)

    # 2) Print the tree
    print("=" * 60)
    print("AGENT TREE")
    print("=" * 60)
    print(tree.visualize())
    print()

    # 3) Run the orchestrator
    hooks = OrchestratorHooks(
        on_node_start=on_node_start,
        on_node_end=on_node_end,
        on_handoff=on_handoff,
    )
    orchestrator = SupervisorOrchestrator(tree=tree, hooks=hooks, max_steps=10)

    print("=" * 60)
    print("ORCHESTRATION RUN")
    print("=" * 60)
    prompt = "Why was invoice #4821 rejected?"
    print(f"  User prompt: {prompt!r}\n")

    result = await orchestrator.run(prompt)

    # 4) Print handoff summaries
    print()
    print("=" * 60)
    print("HANDOFF SUMMARIES")
    print("=" * 60)
    for i, h in enumerate(result.handoffs_received, 1):
        print(f"  [{i}] {h.from_agent} → {h.to_agent}")
        print(f"      status:  {h.status}")
        print(f"      summary: {h.summary}")
        print(f"      tokens:  {h.traces.token_usage}")
        if h.artifacts:
            print(f"      artifacts: {h.artifacts}")
        print()

    # 5) Print final output
    print("=" * 60)
    print("SUPERVISOR FINAL OUTPUT")
    print("=" * 60)
    print(f"  Status:       {result.status}")
    print(f"  Answer:       {result.answer}")
    print(f"  Total steps:  {result.total_steps}")
    print(f"  Total tokens: {result.total_tokens}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
