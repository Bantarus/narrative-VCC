"""Path resolver: walks edges.json from a target node back to root,
then emits an annotated JSONL stream (root-first) for the full ancestor chain."""

import json
import logging
from pathlib import Path
from typing import Iterator

log = logging.getLogger(__name__)

JUNK_TYPES = frozenset({
    '_agent_heartbeat', '_debug_trace', '_scaffold', '_llm_meta',
})


class NodeNotFoundError(KeyError):
    """Target node ID not present in edges.json."""


class NodeFileMissingError(FileNotFoundError):
    """The .jsonl file for a node in the resolved path does not exist."""


class CycleDetectedError(ValueError):
    """A cycle was detected while walking the parent chain."""


class PathResolver:
    def __init__(self, tree_root: str):
        self.tree_root = Path(tree_root)
        self.edges = self._load_edges()

    def resolve_path(self, target_node_id: str) -> list[str]:
        """Return ordered list of node_ids from root -> target (inclusive)."""
        if target_node_id not in self.edges:
            raise NodeNotFoundError(target_node_id)

        chain: list[str] = []
        visited: set[str] = set()
        current = target_node_id

        while current is not None:
            if current in visited:
                raise CycleDetectedError(
                    f"Cycle detected: {current} already visited in chain {chain}")
            visited.add(current)
            chain.append(current)
            parent = self.edges[current].get("parent")
            current = parent

        chain.reverse()
        return chain

    def emit_stream(self, target_node_id: str) -> Iterator[dict]:
        """Yield annotated records for the full ancestor chain, root first.

        Each yielded record has two extra keys:
          _node:  str  -- the node_id this record came from
          _depth: int  -- depth in tree (root=0)

        Junk types are pre-filtered and not yielded.
        Malformed JSON lines are logged and skipped.
        """
        path = self.resolve_path(target_node_id)

        for depth, node_id in enumerate(path):
            node_file = self._node_path(node_id)
            if not node_file.exists():
                raise NodeFileMissingError(
                    f"Missing JSONL file for node '{node_id}': {node_file}")

            with open(node_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as e:
                        log.warning(
                            "Skipping malformed JSON at %s:%d: %s",
                            node_file.name, line_num, e,
                        )
                        continue

                    if record.get("type") in JUNK_TYPES:
                        continue

                    record["_node"] = node_id
                    record["_depth"] = depth
                    yield record

    def _load_edges(self) -> dict:
        edges_path = self.tree_root / "edges.json"
        with open(edges_path, encoding="utf-8") as f:
            return json.load(f)

    def _node_path(self, node_id: str) -> Path:
        """Return path to node_id.jsonl inside tree_root/nodes/."""
        return self.tree_root / "nodes" / f"{node_id}.jsonl"
