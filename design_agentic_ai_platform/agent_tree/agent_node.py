"""
AgentNode — a single node in the hierarchical agent tree.

WHY a tree:  Enterprise agent platforms decompose work into
             Supervisor → Specialist → Verifier chains.  A tree
             makes this hierarchy explicit, inspectable, and
             serialisable (for config-driven construction).
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable

from .handoff_models import HandoffResult


# Type alias for a minimal async agent callable.
# Signature:  async (input: str) -> HandoffResult
AgentCallable = Callable[[str], Awaitable[HandoffResult]]


class AgentNode:
    """One node in the agent hierarchy.

    Can be a Supervisor (root), Specialist (internal), or Leaf agent.
    Each node optionally wraps an async *agent callable* that does the
    real work — the tree itself is just structure + metadata.
    """

    def __init__(
        self,
        node_id: str,
        *,
        name: str | None = None,
        agent: AgentCallable | None = None,
        tools: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.node_id = node_id
        self.name = name or node_id
        self.agent = agent  # async callable; set later if needed
        self.tools: list[str] = tools or []
        self.metadata: dict[str, Any] = metadata or {}

        # Tree linkage
        self.children: list[AgentNode] = []
        self.parent: AgentNode | None = None

    # ── Tree mutations ─────────────────────────────────────────────────

    def add_child(self, node: AgentNode) -> AgentNode:
        """Attach *node* as a child of this node.  Returns the child."""
        node.parent = self
        self.children.append(node)
        return node

    def add_tool(self, tool: str) -> None:
        """Register a tool name this agent can invoke."""
        if tool not in self.tools:
            self.tools.append(tool)

    def set_agent(self, agent: AgentCallable) -> None:
        """Bind an async callable that implements this agent's logic."""
        self.agent = agent

    # ── Queries ────────────────────────────────────────────────────────

    def path(self) -> str:
        """Slash-separated path from root to this node.

        Example: "supervisor/triage/invoice-specialist"
        """
        parts: list[str] = []
        current: AgentNode | None = self
        while current is not None:
            parts.append(current.name)
            current = current.parent
        return "/".join(reversed(parts))

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        d = 0
        current: AgentNode | None = self.parent
        while current is not None:
            d += 1
            current = current.parent
        return d

    # ── Execution ──────────────────────────────────────────────────────

    async def run(self, user_input: str) -> HandoffResult:
        """Execute this node's agent callable.

        Raises RuntimeError if no agent is bound — callers should check
        before invoking.
        """
        if self.agent is None:
            raise RuntimeError(
                f"AgentNode '{self.name}' has no agent callable bound. "
                f"Call set_agent() first."
            )
        return await self.agent(user_input)

    # ── Display ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        tools_str = f", tools={self.tools}" if self.tools else ""
        children_str = f", children={len(self.children)}" if self.children else ""
        return f"AgentNode(id={self.node_id!r}{tools_str}{children_str})"
