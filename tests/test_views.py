"""Tests for narrative.tag_index and narrative.views — Phase 3."""

import shutil
import tempfile
from pathlib import Path

import pytest

from narrative.pipeline import NarrativePipeline
from narrative.tag_index import TagIndex
from narrative.views import render_ui_view, render_adaptive_view, render_transposed_view

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def tree_root():
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


@pytest.fixture
def ir_3node(pipeline):
    """IR for the full 3-node chain: root -> fork_b -> fork_b_1."""
    return pipeline.compile_ir("act1_fork_b_1")


@pytest.fixture
def ir_2node(pipeline):
    """IR for 2-node chain: root -> fork_b."""
    return pipeline.compile_ir("act1_fork_b")


# ── TagIndex tests ──

class TestTagIndex:
    def test_exact_tag_match(self, ir_3node):
        idx = TagIndex(ir_3node)
        results = idx.query("npc:marcus")
        assert len(results) > 0
        for block in results:
            content = "\n".join(block.get("content", []))
            assert "marcus" in content.lower() or "npc:marcus" in content.lower()

    def test_prefix_match(self, ir_3node):
        idx = TagIndex(ir_3node)
        results = idx.query("npc:")
        assert len(results) > 0

    def test_bare_tag_match(self, ir_3node):
        idx = TagIndex(ir_3node)
        results = idx.query("continuity")
        assert len(results) > 0
        # All should be arc_note blocks
        for block in results:
            assert block["type"] == "arc_note"

    def test_substring_fallback(self, ir_2node):
        idx = TagIndex(ir_2node)
        results = idx.query("tavern")
        assert len(results) > 0
        # Should match scene content mentioning tavern
        found = False
        for block in results:
            content = "\n".join(block.get("content", []))
            if "tavern" in content.lower():
                found = True
        assert found

    def test_and_composition(self, ir_3node):
        idx = TagIndex(ir_3node)
        # npc:marcus AND continuity — should match arc_notes about marcus
        results = idx.query_all(["npc:marcus", "continuity"])
        assert len(results) > 0
        for block in results:
            content = "\n".join(block.get("content", []))
            assert "npc:marcus" in content.lower() or "marcus" in content.lower()
            assert "continuity" in content.lower()

    def test_empty_query_returns_all(self, ir_2node):
        idx = TagIndex(ir_2node)
        results = idx.query("")
        assert len(results) == len(idx.blocks)

    def test_no_match_returns_empty(self, ir_2node):
        idx = TagIndex(ir_2node)
        results = idx.query("nonexistent:tag")
        assert results == []


# ── UI View tests ──

class TestUIView:
    def test_full_render(self, ir_3node):
        output = render_ui_view(ir_3node)
        assert "act1_root" in output
        assert "act1_fork_b" in output
        assert "act1_fork_b_1" in output
        assert "══════════════════════════════" in output

    def test_grep_filtered(self, ir_3node):
        output = render_ui_view(ir_3node, grep_exprs=["npc:marcus"])
        assert "marcus" in output.lower()

    def test_scene_content_present(self, ir_3node):
        output = render_ui_view(ir_3node)
        assert "The tavern falls silent" in output

    def test_arc_note_bordered(self, ir_2node):
        output = render_ui_view(ir_2node)
        assert ">>>arc_note" in output
        assert "<<<arc_note" in output


# ── Adaptive View tests ──

class TestAdaptiveView:
    def test_default_shows_continuity(self, ir_3node):
        """Without grep, adaptive view shows arc_note + world_state."""
        output = render_adaptive_view(ir_3node)
        assert "ARC_NOTE" in output
        assert "WORLD_STATE" in output

    def test_with_grep(self, ir_3node):
        output = render_adaptive_view(ir_3node, grep_exprs=["npc:marcus"])
        assert "marcus" in output.lower()


# ── Transposed View tests ──

class TestTransposedView:
    def test_sorted_by_depth(self, ir_3node):
        output = render_transposed_view(ir_3node, grep_exprs=["npc:marcus"])
        lines = output.split("\n")
        # Extract depth values from header lines
        depths = []
        for line in lines:
            if line.startswith("[") and "depth:" in line:
                depth = int(line.split("depth:")[1].split("]")[0])
                depths.append(depth)
        # Depths should be non-decreasing
        for i in range(1, len(depths)):
            assert depths[i] >= depths[i - 1]

    def test_contains_source_node(self, ir_3node):
        output = render_transposed_view(ir_3node, grep_exprs=["continuity"])
        # Should contain the node IDs of blocks with continuity tag
        assert "act1_fork_b" in output

    def test_line_references(self, ir_3node):
        output = render_transposed_view(ir_3node, grep_exprs=["npc:marcus"])
        # Should contain line references
        assert "lines" in output
