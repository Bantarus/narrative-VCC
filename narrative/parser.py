"""Narrative parser: converts LexTokens into VCC-compatible IR node dicts."""

from __future__ import annotations

from typing import Iterator

from narrative.lexer import LexToken

# ── Separator line, same as upstream VCC ──
SEP = "══════════════════════════════"


def _node(typ: str, content: list[str], **kw) -> dict:
    """Create a VCC-compatible IR node dict."""
    o = {"type": typ, "content": content,
         "searchable": kw.pop("searchable", False)}
    o.update(kw)
    return o


def _format_delta(delta: dict) -> list[str]:
    """Render a world_state delta as YAML-style diff lines."""
    lines = []
    for key, val in delta.items():
        lines.append(f"  {key}: {val}")
    return lines


class NarrativeParser:
    """Converts LexTokens from NarrativeLexer into a flat list of VCC IR nodes.

    The IR output is structurally compatible with VCC's assign_lines / lower / emit
    pipeline. Each narrative record becomes a section (_sec) with a header and content.
    """

    def parse(self, tokens: Iterator[LexToken]) -> list[dict]:
        ir: list[dict] = []
        sec = 0
        blk = 0

        for token in tokens:
            p = token.payload
            node_id = token.node_id
            depth = token.depth
            tags = p.get("tags", [])
            tag_line = ", ".join(tags) if tags else None

            # Separator between sections (skip before the very first)
            if sec > 0:
                ir.append(_node("meta", ["", SEP]))

            if token.type == "scene":
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] SCENE", ""],
                                _sec=sec))
                lines = [f"  {line}" for line in p.get("content", "").split("\n")]
                if tag_line:
                    lines.append(f"  tags: {tag_line}")
                ir.append(_node("scene", lines, searchable=True,
                                _sec=sec, _blk=blk,
                                _node=node_id, _depth=depth))
                blk += 1

            elif token.type == "npc_dialogue":
                speaker = p.get("speaker", "???")
                disposition = p.get("disposition", "")
                disp_str = f"  (disposition: {disposition})" if disposition else ""
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] NPC_DIALOGUE — {speaker}{disp_str}", ""],
                                _sec=sec))
                content_text = p.get("content", "")
                lines = [f'  "{content_text}"']
                if tag_line:
                    lines.append(f"  tags: {tag_line}")
                ir.append(_node("npc_dialogue", lines, searchable=True,
                                _sec=sec, _blk=blk,
                                _speaker=speaker, _disposition=disposition,
                                _node=node_id, _depth=depth))
                blk += 1

            elif token.type == "player_choice":
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] PLAYER_CHOICE", ""],
                                _sec=sec))
                prompt = p.get("prompt", "")
                options = p.get("options", [])
                chosen = p.get("chosen")
                lines = [f"  Prompt: {prompt}"]
                for opt in options:
                    if opt == chosen:
                        lines.append(f"  \u2605 {opt}         \u2190 chosen")
                    else:
                        lines.append(f"  > {opt}")
                if tag_line:
                    lines.append(f"  tags: {tag_line}")
                ir.append(_node("player_choice", lines, searchable=True,
                                _sec=sec, _blk=blk,
                                _chosen=chosen,
                                _node=node_id, _depth=depth))
                blk += 1

            elif token.type == "consequence":
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] CONSEQUENCE", ""],
                                _sec=sec))
                lines = [f"  {line}" for line in p.get("content", "").split("\n")]
                if tag_line:
                    lines.append(f"  tags: {tag_line}")
                ir.append(_node("consequence", lines, searchable=True,
                                _sec=sec, _blk=blk,
                                _node=node_id, _depth=depth))
                blk += 1

            elif token.type == "world_state":
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] WORLD_STATE", ""],
                                _sec=sec))
                delta = p.get("delta", {})
                lines = ["  delta:"] + _format_delta(delta) if delta else []
                flags = p.get("flags", {})
                if flags:
                    if lines:
                        lines.append("")
                    lines.append("  flags:")
                    for k, v in flags.items():
                        lines.append(f"    {k}: {v}")
                ir.append(_node("world_state", lines, searchable=True,
                                _sec=sec, _blk=blk,
                                _node=node_id, _depth=depth))
                blk += 1

            elif token.type == "arc_note":
                author = p.get("author", "unknown")
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] ARC_NOTE  \u25c6 {author}", ""],
                                _sec=sec))
                # arc_note maps to VCC's "thinking" role visually
                ir.append(_node("meta", [f">>>arc_note"], _sec=sec, _blk=blk))
                lines = [f"  {line}" for line in p.get("content", "").split("\n")]
                if tag_line:
                    lines.append(f"  tags: {tag_line}")
                ir.append(_node("arc_note", lines, searchable=True,
                                _sec=sec, _blk=blk,
                                _author=author,
                                _node=node_id, _depth=depth))
                ir.append(_node("meta", ["<<<arc_note"], _sec=sec, _blk=blk))
                blk += 1

            elif token.type == "branch_point":
                children = p.get("children", [])
                taken = p.get("taken")
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] BRANCH_POINT", ""],
                                _sec=sec))
                lines = []
                for child in children:
                    marker = " \u2190 taken" if child == taken else ""
                    lines.append(f"  \u2192 {child}{marker}")
                ir.append(_node("branch_point", lines, searchable=True,
                                _sec=sec, _blk=blk,
                                _children=children, _taken=taken,
                                _node=node_id, _depth=depth))
                blk += 1

            elif token.type == "unknown":
                ir.append(_node("meta_header",
                                [f"[{node_id} / depth:{depth}] UNKNOWN", ""],
                                _sec=sec))
                import json
                ir.append(_node("unknown",
                                [f"  {json.dumps(p, default=str)}"],
                                searchable=True,
                                _sec=sec, _blk=blk,
                                _node=node_id, _depth=depth))
                blk += 1

            sec += 1

        # Trailing newline node (matches VCC convention)
        ir.append(_node("meta", [""]))
        return ir
