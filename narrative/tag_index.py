"""Tag-aware index and query engine for narrative IR blocks."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Sequence


class TagIndex:
    """Index built from IR blocks produced by the narrative parser.

    Supports queries:
      npc:marcus           -> all blocks tagged npc:marcus
      arc:marcus_conflict  -> all blocks tagged arc:marcus_conflict
      choice:              -> all blocks whose tags have prefix "choice:"
      continuity           -> all blocks tagged with "continuity" (exact match)
      "some text"          -> bare string with no colon falls back to substring
                              match on content (VCC-compatible grep)

    Multiple queries composed with AND: a block must match ALL expressions.
    """

    def __init__(self, blocks: list[dict]):
        self.blocks = [b for b in blocks if b.get("searchable")]
        self._tag_to_blocks: dict[str, list[dict]] = defaultdict(list)
        self._prefix_to_blocks: dict[str, list[dict]] = defaultdict(list)
        self._build()

    def _build(self):
        for block in self.blocks:
            tags = block.get("_tags", [])
            # Also look for tags embedded in content lines (tags: x, y, z)
            if not tags:
                tags = self._extract_tags_from_content(block)
            for tag in tags:
                self._tag_to_blocks[tag].append(block)
                if ":" in tag:
                    prefix = tag.split(":")[0] + ":"
                    self._prefix_to_blocks[prefix].append(block)

    def _extract_tags_from_content(self, block: dict) -> list[str]:
        """Extract tags from content lines like '  tags: npc:marcus, continuity'."""
        for line in block.get("content", []):
            stripped = line.strip()
            if stripped.startswith("tags:"):
                tag_str = stripped[len("tags:"):].strip()
                return [t.strip() for t in tag_str.split(",") if t.strip()]
        return []

    def query(self, expr: str) -> list[dict]:
        """Query for blocks matching a single expression."""
        expr = expr.strip()
        if not expr:
            return list(self.blocks)

        # Tag with colon but no value: prefix match (e.g., "choice:")
        if expr.endswith(":"):
            return list(self._prefix_to_blocks.get(expr, []))

        # Tag with colon and value: exact tag match (e.g., "npc:marcus")
        if ":" in expr:
            return list(self._tag_to_blocks.get(expr, []))

        # Bare string: first try exact tag match, then fall back to substring
        if expr in self._tag_to_blocks:
            return list(self._tag_to_blocks[expr])

        # Substring match on content (VCC-compatible grep fallback)
        return self._substring_match(expr)

    def query_all(self, expressions: list[str]) -> list[dict]:
        """AND-compose multiple queries: return blocks matching ALL expressions."""
        if not expressions:
            return list(self.blocks)

        result_sets = []
        for expr in expressions:
            matches = self.query(expr)
            result_sets.append(set(id(b) for b in matches))

        if not result_sets:
            return []

        common_ids = result_sets[0]
        for s in result_sets[1:]:
            common_ids &= s

        return [b for b in self.blocks if id(b) in common_ids]

    def _substring_match(self, text: str) -> list[dict]:
        """Fall back to substring match on block content."""
        text_lower = text.lower()
        results = []
        for block in self.blocks:
            content = "\n".join(block.get("content", []))
            if text_lower in content.lower():
                results.append(block)
        return results
