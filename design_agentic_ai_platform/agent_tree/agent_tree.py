"""
AgentTree — hierarchical agent tree with visualisation and lookup.

WHY a dedicated tree class (vs. bare nodes):
  - visualize() makes the hierarchy inspectable in logs / interviews
  - find() lets the Supervisor look up children by name at runtime
  - Single root constraint enforces the Supervisor-at-top invariant
"""

from __future__ import annotations

from .agent_node import AgentNode


class AgentTree:
    """Wrapper around a rooted tree of AgentNodes.

    The root is always the Supervisor.
    """

    def __init__(self, root: AgentNode) -> None:
        self.root = root

    # ── Lookup ─────────────────────────────────────────────────────────

    def find(self, name: str) -> AgentNode | None:
        """BFS lookup by node name.  Returns None if not found."""
        queue: list[AgentNode] = [self.root]
        while queue:
            node = queue.pop(0)
            if node.name == name:
                return node
            queue.extend(node.children)
        return None

    # ── Visualisation ──────────────────────────────────────────────────

    def visualize(self) -> str:
        """Return a human-readable ASCII tree.

        Example output:
            supervisor (root)
            ├── triage-agent [tools: classify]
            │   ├── invoice-specialist [tools: erp_lookup]
            │   └── refund-specialist [tools: refund_api]
            └── verifier [tools: policy_check]
        """
        lines: list[str] = []
        self._build_lines(self.root, "", True, lines, is_root=True)
        return "\n".join(lines)

    # ── Internals ──────────────────────────────────────────────────────

    @staticmethod
    def _build_lines(
        node: AgentNode,
        prefix: str,
        is_last: bool,
        lines: list[str],
        *,
        is_root: bool = False,
    ) -> None:
        # Connector glyph
        if is_root:
            connector = ""
        elif is_last:
            connector = "└── "
        else:
            connector = "├── "

        # Node label
        tools_tag = f" [tools: {', '.join(node.tools)}]" if node.tools else ""
        root_tag = " (root)" if is_root else ""
        lines.append(f"{prefix}{connector}{node.name}{root_tag}{tools_tag}")

        # Child prefix
        if is_root:
            child_prefix = prefix
        elif is_last:
            child_prefix = prefix + "    "
        else:
            child_prefix = prefix + "│   "

        for i, child in enumerate(node.children):
            AgentTree._build_lines(
                child,
                child_prefix,
                is_last=(i == len(node.children) - 1),
                lines=lines,
            )

    def __repr__(self) -> str:
        return f"AgentTree(root={self.root.name!r}, nodes={self._count()})"

    def _count(self) -> int:
        """Total nodes in the tree."""
        return self._count_recursive(self.root)

    @staticmethod
    def _count_recursive(node: AgentNode) -> int:
        return 1 + sum(AgentTree._count_recursive(c) for c in node.children)
