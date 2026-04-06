"""Tests for narrative.path_resolver — Phase 1."""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from narrative.path_resolver import (
    CycleDetectedError,
    NodeFileMissingError,
    NodeNotFoundError,
    PathResolver,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def resolver():
    """PathResolver pointed at the test fixtures directory (used as tree_root)."""
    # The fixtures dir has edges.json and .jsonl files directly (no nodes/ subdir),
    # so we set up a temp tree that mirrors the expected layout.
    tmp = tempfile.mkdtemp()
    # Copy edges.json
    shutil.copy(FIXTURES / "edges.json", Path(tmp) / "edges.json")
    # Copy node files into nodes/
    nodes_dir = Path(tmp) / "nodes"
    nodes_dir.mkdir()
    for f in FIXTURES.glob("*.jsonl"):
        shutil.copy(f, nodes_dir / f.name)
    yield PathResolver(tmp)
    shutil.rmtree(tmp)


class TestResolvePath:
    def test_root_only(self, resolver):
        path = resolver.resolve_path("act1_root")
        assert path == ["act1_root"]

    def test_two_depth(self, resolver):
        path = resolver.resolve_path("act1_fork_b")
        assert path == ["act1_root", "act1_fork_b"]

    def test_three_depth(self, resolver):
        path = resolver.resolve_path("act1_fork_b_1")
        assert path == ["act1_root", "act1_fork_b", "act1_fork_b_1"]

    def test_alternative_branch(self, resolver):
        path = resolver.resolve_path("act1_fork_a")
        assert path == ["act1_root", "act1_fork_a"]


class TestEmitStream:
    def test_root_only_stream(self, resolver):
        records = list(resolver.emit_stream("act1_root"))
        assert len(records) > 0
        # All records should come from act1_root at depth 0
        for r in records:
            assert r["_node"] == "act1_root"
            assert r["_depth"] == 0

    def test_two_depth_stream(self, resolver):
        records = list(resolver.emit_stream("act1_fork_b"))
        nodes_seen = [r["_node"] for r in records]
        # Root records come first, then fork_b records
        root_indices = [i for i, n in enumerate(nodes_seen) if n == "act1_root"]
        fork_indices = [i for i, n in enumerate(nodes_seen) if n == "act1_fork_b"]
        assert len(root_indices) > 0
        assert len(fork_indices) > 0
        assert max(root_indices) < min(fork_indices)

    def test_three_depth_stream(self, resolver):
        records = list(resolver.emit_stream("act1_fork_b_1"))
        nodes_seen = [r["_node"] for r in records]
        unique_nodes = list(dict.fromkeys(nodes_seen))  # preserve order, dedup
        assert unique_nodes == ["act1_root", "act1_fork_b", "act1_fork_b_1"]

    def test_depth_annotation(self, resolver):
        records = list(resolver.emit_stream("act1_fork_b_1"))
        for r in records:
            if r["_node"] == "act1_root":
                assert r["_depth"] == 0
            elif r["_node"] == "act1_fork_b":
                assert r["_depth"] == 1
            elif r["_node"] == "act1_fork_b_1":
                assert r["_depth"] == 2

    def test_junk_skipped(self, resolver):
        records = list(resolver.emit_stream("act1_fork_b"))
        junk_types = {"_agent_heartbeat", "_debug_trace", "_scaffold", "_llm_meta"}
        for r in records:
            assert r["type"] not in junk_types

    def test_junk_skipped_all_nodes(self, resolver):
        """Junk records are filtered across all nodes in a 3-depth chain."""
        records = list(resolver.emit_stream("act1_fork_b_1"))
        junk_types = {"_agent_heartbeat", "_debug_trace", "_scaffold", "_llm_meta"}
        for r in records:
            assert r["type"] not in junk_types


class TestErrors:
    def test_missing_node_error(self, resolver):
        with pytest.raises(NodeNotFoundError):
            resolver.resolve_path("nonexistent_node")

    def test_missing_file_error(self, resolver):
        # Add a node to edges that has no corresponding .jsonl file
        resolver.edges["phantom_node"] = {"parent": "act1_root"}
        with pytest.raises(NodeFileMissingError):
            list(resolver.emit_stream("phantom_node"))

    def test_cycle_detected(self, resolver):
        # Create a cycle: act1_root -> act1_fork_a -> act1_root
        resolver.edges["act1_root"]["parent"] = "act1_fork_a"
        with pytest.raises(CycleDetectedError):
            resolver.resolve_path("act1_fork_a")


class TestMalformedJson:
    def test_malformed_line_skipped(self, resolver):
        """Malformed JSON lines are skipped, valid lines still emitted."""
        # Write a node file with a bad line
        bad_node = resolver.tree_root / "nodes" / "bad_node.jsonl"
        bad_node.write_text(
            '{"type":"scene","id":"s099","content":"Valid line.","tags":[]}\n'
            'NOT VALID JSON\n'
            '{"type":"consequence","id":"r099","content":"Also valid.","tags":[]}\n'
        )
        resolver.edges["bad_node"] = {"parent": None}
        records = list(resolver.emit_stream("bad_node"))
        assert len(records) == 2
        assert records[0]["id"] == "s099"
        assert records[1]["id"] == "r099"
