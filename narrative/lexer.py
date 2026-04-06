"""Narrative lexer: filters junk, emits typed LexTokens from the annotated stream."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterator

log = logging.getLogger(__name__)

JUNK_TYPES = frozenset({
    '_agent_heartbeat', '_debug_trace', '_scaffold', '_llm_meta',
})

NARRATIVE_TYPES = frozenset({
    'scene', 'npc_dialogue', 'player_choice',
    'consequence', 'world_state', 'arc_note', 'branch_point',
})


@dataclass
class LexToken:
    type: str
    payload: dict[str, Any]
    node_id: str
    depth: int


class NarrativeLexer:
    """Drops junk types, emits LexToken for known narrative types,
    and emits LexToken(type='unknown') for unrecognized types with a warning."""

    def lex(self, stream: Iterator[dict]) -> Iterator[LexToken]:
        for record in stream:
            rtype = record.get("type", "")

            # Junk already filtered by PathResolver, but double-check
            if rtype in JUNK_TYPES:
                continue

            node_id = record.get("_node", "")
            depth = record.get("_depth", 0)

            if rtype in NARRATIVE_TYPES:
                yield LexToken(
                    type=rtype,
                    payload=record,
                    node_id=node_id,
                    depth=depth,
                )
            else:
                log.warning("Unknown record type %r in node %s", rtype, node_id)
                yield LexToken(
                    type="unknown",
                    payload=record,
                    node_id=node_id,
                    depth=depth,
                )
