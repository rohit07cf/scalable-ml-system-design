"""
agent_tree — Hierarchical agent tree with structured handoffs.

Quick usage:

    from agent_tree import AgentNode, AgentTree, HandoffResult, SupervisorOrchestrator

    root = AgentNode("supervisor")
    root.add_child(AgentNode("triage", tools=["classify"]))
    tree = AgentTree(root)
    print(tree.visualize())
"""

from .agent_node import AgentNode
from .agent_tree import AgentTree
from .handoff_models import HandoffResult, HandoffTraces, SupervisorResult
from .orchestrator import OrchestratorHooks, SupervisorOrchestrator

__all__ = [
    "AgentNode",
    "AgentTree",
    "HandoffResult",
    "HandoffTraces",
    "SupervisorResult",
    "OrchestratorHooks",
    "SupervisorOrchestrator",
]
