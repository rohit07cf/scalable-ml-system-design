"""
agent_tree — Hierarchical agent tree with structured handoffs.

Quick usage:

    from agent_tree import AgentNode, AgentTree, HandoffResult, SupervisorOrchestrator

    root = AgentNode("supervisor")
    root.add_child(AgentNode("triage", tools=["classify"]))
    tree = AgentTree(root)
    print(tree.visualize())
"""

from .agent_node import AgentNode, AgentCallable, ToolCallable
from .agent_tree import AgentTree
from .handoff_models import HandoffResult, HandoffTraces, ToolResult, SupervisorResult
from .orchestrator import OrchestratorHooks, SupervisorOrchestrator, PlannerCallable

__all__ = [
    "AgentNode",
    "AgentCallable",
    "ToolCallable",
    "AgentTree",
    "HandoffResult",
    "HandoffTraces",
    "ToolResult",
    "SupervisorResult",
    "OrchestratorHooks",
    "SupervisorOrchestrator",
    "PlannerCallable",
]
