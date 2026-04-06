"""Tests for narrative.pipeline — Phase 2 integration tests.

These validate that the full pipeline (PathResolver -> Lexer -> Parser -> VCC IR)
produces correct IR output from fixture data.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from narrative.pipeline import NarrativePipeline

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def tree_root():
    """Set up a temp tree that mirrors the expected layout."""
    tmp = tempfile.mkdtemp()
    shutil.copy(FIXTURES / "edges.json", Path(tmp) / "edges.json")
    nodes_dir = Path(tmp) / "nodes"
    nodes_dir.mkdir()
    for f in FIXTURES.glob("*.jsonl"):
        shutil.copy(f, nodes_dir / f.name)
    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def pipeline(tree_root):
    return NarrativePipeline(tree_root)


class TestIRStructure:
    def test_ir_nodes_have_required_keys(self, pipeline):
        ir = pipeline.compile_ir("act1_root")
        for node in ir:
            assert "type" in node
            assert "content" in node
            assert "searchable" in node

    def test_line_numbers_assigned(self, pipeline):
        ir = pipeline.compile_ir("act1_root")
        searchable = [n for n in ir if n.get("searchable")]
        for node in searchable:
            assert "start_line" in node
            assert "end_line" in node
            assert node["start_line"] <= node["end_line"]

    def test_line_numbers_monotonic(self, pipeline):
        ir = pipeline.compile_ir("act1_fork_b_1")
        lines = []
        for node in ir:
            if "start_line" in node:
                lines.append((node["start_line"], node["end_line"]))
        # Start lines should be non-decreasing
        for i in range(1, len(lines)):
            assert lines[i][0] >= lines[i - 1][0]


class TestThreeNodeChain:
    """The critical phase gate: 3-node chain must produce correct IR."""

    def test_three_node_chain_nodes_present(self, pipeline):
        ir = pipeline.compile_ir("act1_fork_b_1")
        nodes_in_ir = set()
        for n in ir:
            if "_node" in n:
                nodes_in_ir.add(n["_node"])
        assert "act1_root" in nodes_in_ir
        assert "act1_fork_b" in nodes_in_ir
        assert "act1_fork_b_1" in nodes_in_ir

    def test_three_node_chain_ordering(self, pipeline):
        ir = pipeline.compile_ir("act1_fork_b_1")
        # Collect node appearance order from searchable blocks
        seen_order = []
        for n in ir:
            node_id = n.get("_node")
            if node_id and node_id not in seen_order:
                seen_order.append(node_id)
        assert seen_order == ["act1_root", "act1_fork_b", "act1_fork_b_1"]

    def test_three_node_chain_depths(self, pipeline):
        ir = pipeline.compile_ir("act1_fork_b_1")
        for n in ir:
            node_id = n.get("_node")
            depth = n.get("_depth")
            if node_id == "act1_root":
                assert depth == 0
            elif node_id == "act1_fork_b":
                assert depth == 1
            elif node_id == "act1_fork_b_1":
                assert depth == 2

    def test_no_junk_in_ir(self, pipeline):
        ir = pipeline.compile_ir("act1_fork_b_1")
        junk = {"_agent_heartbeat", "_debug_trace", "_scaffold", "_llm_meta"}
        for n in ir:
            assert n["type"] not in junk

    def test_all_record_types_present(self, pipeline):
        """The 3-node chain includes scene, npc_dialogue, player_choice,
        consequence, world_state, arc_note, and branch_point."""
        ir = pipeline.compile_ir("act1_fork_b_1")
        types = {n["type"] for n in ir if n.get("searchable")}
        assert "scene" in types
        assert "npc_dialogue" in types
        assert "player_choice" in types
        assert "consequence" in types
        assert "world_state" in types
        assert "arc_note" in types
        assert "branch_point" in types


class TestFullOutput:
    def test_full_view_renders(self, pipeline):
        output = pipeline.compile("act1_fork_b_1", view="full")
        assert isinstance(output, str)
        assert len(output) > 0
        # Should contain node headers
        assert "act1_root" in output
        assert "act1_fork_b" in output
        assert "act1_fork_b_1" in output

    def test_full_view_contains_sep(self, pipeline):
        output = pipeline.compile("act1_fork_b_1", view="full")
        assert "══════════════════════════════" in output

    def test_full_view_scene_content(self, pipeline):
        output = pipeline.compile("act1_root", view="full")
        assert "The tavern falls silent as you enter." in output

    def test_full_view_npc_dialogue(self, pipeline):
        output = pipeline.compile("act1_root", view="full")
        assert "Marcus" in output
        assert "You shouldn't be here." in output

    def test_full_view_arc_note_markers(self, pipeline):
        output = pipeline.compile("act1_fork_b", view="full")
        assert ">>>arc_note" in output
        assert "<<<arc_note" in output

    def test_brief_view_renders(self, pipeline):
        output = pipeline.compile("act1_root", view="brief")
        assert isinstance(output, str)

    def test_root_only_view(self, pipeline):
        output = pipeline.compile("act1_root", view="full")
        # Should NOT contain fork_b content
        assert "act1_fork_b" not in output or "act1_fork_b" in output.split("BRANCH_POINT")[1] if "BRANCH_POINT" in output else True
