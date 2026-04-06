"""Tests for narrative.lexer — Phase 2."""

import pytest

from narrative.lexer import LexToken, NarrativeLexer, JUNK_TYPES, NARRATIVE_TYPES


@pytest.fixture
def lexer():
    return NarrativeLexer()


def _make_record(rtype, **kw):
    r = {"type": rtype, "_node": "test_node", "_depth": 0}
    r.update(kw)
    return r


class TestLexerFiltering:
    def test_junk_dropped(self, lexer):
        stream = [_make_record(t) for t in JUNK_TYPES]
        tokens = list(lexer.lex(iter(stream)))
        assert tokens == []

    def test_known_types_emitted(self, lexer):
        stream = [_make_record(t) for t in NARRATIVE_TYPES]
        tokens = list(lexer.lex(iter(stream)))
        types = {tok.type for tok in tokens}
        assert types == NARRATIVE_TYPES

    def test_unknown_type_emitted_as_unknown(self, lexer):
        stream = [_make_record("exotic_new_type", id="x1")]
        tokens = list(lexer.lex(iter(stream)))
        assert len(tokens) == 1
        assert tokens[0].type == "unknown"
        assert tokens[0].payload["type"] == "exotic_new_type"


class TestLexTokenFields:
    def test_node_and_depth_carried_through(self, lexer):
        stream = [_make_record("scene", _node="act1_root", _depth=0, id="s1",
                               content="test", tags=[])]
        tokens = list(lexer.lex(iter(stream)))
        assert tokens[0].node_id == "act1_root"
        assert tokens[0].depth == 0

    def test_payload_is_full_record(self, lexer):
        rec = _make_record("npc_dialogue", speaker="Marcus",
                           content="Hello", disposition="neutral", tags=[])
        tokens = list(lexer.lex(iter([rec])))
        assert tokens[0].payload["speaker"] == "Marcus"

    def test_mixed_stream_ordering(self, lexer):
        stream = [
            _make_record("scene", id="s1", content="A", tags=[]),
            _make_record("_agent_heartbeat"),
            _make_record("npc_dialogue", id="d1", speaker="X",
                         content="B", disposition="", tags=[]),
            _make_record("_debug_trace"),
            _make_record("consequence", id="r1", content="C", tags=[]),
        ]
        tokens = list(lexer.lex(iter(stream)))
        assert len(tokens) == 3
        assert [t.type for t in tokens] == ["scene", "npc_dialogue", "consequence"]
