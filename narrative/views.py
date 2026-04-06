"""Narrative-specific view renderers.

These produce human-readable output from IR blocks, with node-of-origin labels
and cross-view line-number pointers.
"""

from __future__ import annotations

import sys
import os

_VCC_DIR = os.path.join(os.path.dirname(__file__), "..",
                        "skills", "conversation-compiler", "scripts")
if _VCC_DIR not in sys.path:
    sys.path.insert(0, _VCC_DIR)

import VCC as _vcc

from narrative.tag_index import TagIndex

SEP = "══════════════════════════════"


def render_ui_view(ir: list[dict], grep_exprs: list[str] | None = None) -> str:
    """Render the narrative UI view — primary human-readable format.

    If grep_exprs are provided, only matching blocks are shown (via TagIndex).
    Otherwise, the full IR is rendered.
    """
    if grep_exprs:
        index = TagIndex(ir)
        matched = index.query_all(grep_exprs)
        matched_ids = set(id(b) for b in matched)
        # Build a filtered IR: include matched blocks and their headers/separators
        filtered = _filter_ir_to_matched(ir, matched_ids)
        lines = _vcc.emit(filtered, "content")
    else:
        lines = _vcc.emit(ir, "content")

    return "\n".join(lines)


def render_adaptive_view(ir: list[dict], grep_exprs: list[str] | None = None) -> str:
    """Adaptive view: if grep is provided, show only matching blocks.
    Otherwise, show a minimal continuity snapshot (arc_note + world_state)."""
    if not grep_exprs:
        grep_exprs = []
        # Default: show arc_note and world_state blocks for continuity
        matched = [b for b in ir
                   if b.get("searchable") and b["type"] in ("arc_note", "world_state")]
    else:
        index = TagIndex(ir)
        matched = index.query_all(grep_exprs)

    matched_ids = set(id(b) for b in matched)
    filtered = _filter_ir_to_matched(ir, matched_ids)
    lines = _vcc.emit(filtered, "content")
    return "\n".join(lines)


def render_transposed_view(ir: list[dict], grep_exprs: list[str]) -> str:
    """Transposed view: results sorted by depth, each tagged with source node.

    Used by /narrative-search for cross-tree queries.
    """
    index = TagIndex(ir)
    matched = index.query_all(grep_exprs)

    # Sort by depth (shallow first), then by start_line
    matched.sort(key=lambda b: (b.get("_depth", 0), b.get("start_line", 0)))

    out_lines = []
    for block in matched:
        node_id = block.get("_node", "?")
        depth = block.get("_depth", 0)
        btype = block["type"].upper()
        start = block.get("start_line", 0) + 1
        end = block.get("end_line", 0) + 1

        out_lines.append(f"[{node_id} / depth:{depth}] {btype} (lines {start}-{end})")
        for line in block.get("content", []):
            out_lines.append(line)
        out_lines.append("")

    return "\n".join(out_lines)


def _filter_ir_to_matched(ir: list[dict], matched_ids: set[int]) -> list[dict]:
    """Build a filtered IR that includes only matched blocks and their
    associated headers/separators. Non-matching blocks get content=None
    so _walk skips them."""
    filtered = []
    # Determine which sections have visible blocks
    visible_secs = set()
    for node in ir:
        if id(node) in matched_ids:
            sec = node.get("_sec")
            if sec is not None:
                visible_secs.add(sec)

    for node in ir:
        sec = node.get("_sec")

        # Separator between sections
        if node["type"] == "meta" and SEP in node.get("content", []):
            filtered.append(node)
            continue

        # Meta headers: show if their section has visible blocks
        if node["type"] == "meta_header":
            if sec in visible_secs:
                filtered.append(node)
            continue

        # arc_note markers (>>>arc_note / <<<arc_note): show if blk is visible
        if node["type"] == "meta":
            content = node.get("content", [])
            if content and (content[0].startswith(">>>arc_note") or
                            content[0] == "<<<arc_note"):
                blk = node.get("_blk")
                # Find if any block in same sec/blk is matched
                blk_matched = any(
                    id(n) in matched_ids
                    for n in ir
                    if n.get("_blk") == blk and n.get("_sec") == sec
                )
                if blk_matched:
                    filtered.append(node)
                continue

        # Searchable content: include only if matched
        if id(node) in matched_ids:
            filtered.append(node)
            continue

        # Trailing meta (empty line) — always include
        if node["type"] == "meta" and node.get("content") == [""]:
            filtered.append(node)

    # Clean up: remove consecutive separators for sections with no visible content
    return _clean_separators(filtered, visible_secs)


def _clean_separators(ir: list[dict], visible_secs: set[int]) -> list[dict]:
    """Remove separators that don't border visible sections."""
    result = []
    for i, node in enumerate(ir):
        if node["type"] == "meta" and SEP in node.get("content", []):
            # Look ahead to see if next section is visible
            next_sec = None
            for j in range(i + 1, len(ir)):
                s = ir[j].get("_sec")
                if s is not None:
                    next_sec = s
                    break
            # Look back for prev visible section
            prev_visible = False
            for j in range(i - 1, -1, -1):
                s = ir[j].get("_sec")
                if s is not None and s in visible_secs:
                    prev_visible = True
                    break
            if next_sec in visible_secs and prev_visible:
                result.append(node)
        else:
            result.append(node)
    return result
