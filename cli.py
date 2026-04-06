#!/usr/bin/env python3
"""CLI entry point for VCC-Narrative.

Usage:
  python cli.py recall  --node act1_fork_b_1 [--grep EXPR ...] [--view ui|full|brief|adaptive|transposed]
  python cli.py branch  --node act1_fork_b   --choice "Threaten Marcus"
  python cli.py search  --tree ./tree        --grep EXPR [--view adaptive|transposed]
  python cli.py inspect --node act1_fork_b   [--tree ./tree]
"""

import argparse
import json
import os
import re
import sys

from narrative.pipeline import NarrativePipeline
from narrative.path_resolver import (
    PathResolver, NodeNotFoundError, NodeFileMissingError, CycleDetectedError,
)
from narrative.tag_index import TagIndex
from narrative.views import render_ui_view, render_adaptive_view, render_transposed_view


def _tree_root(args):
    return getattr(args, "tree", None) or os.environ.get("NARRATIVE_TREE_ROOT", "./tree")


def _node_id(args):
    node = getattr(args, "node", None) or os.environ.get("CURRENT_NODE")
    if not node:
        print("Error: --node is required (or set CURRENT_NODE env var)", file=sys.stderr)
        sys.exit(1)
    return node


def cmd_recall(args):
    tree = _tree_root(args)
    node = _node_id(args)
    pipeline = NarrativePipeline(tree)

    view = args.view or "adaptive"
    grep_exprs = args.grep or []

    if view in ("full", "ui"):
        ir = pipeline.compile_ir(node)
        if grep_exprs:
            output = render_ui_view(ir, grep_exprs=grep_exprs)
        else:
            output = render_ui_view(ir)
    elif view == "brief":
        output = pipeline.compile(node, view="brief")
    elif view == "adaptive":
        ir = pipeline.compile_ir(node)
        output = render_adaptive_view(ir, grep_exprs=grep_exprs if grep_exprs else None)
    elif view == "transposed":
        ir = pipeline.compile_ir(node)
        if not grep_exprs:
            grep_exprs = ["arc_note", "world_state"]
        output = render_transposed_view(ir, grep_exprs=grep_exprs)
    else:
        print(f"Error: unknown view '{view}'", file=sys.stderr)
        sys.exit(1)

    print(output)


def cmd_branch(args):
    tree = _tree_root(args)
    node = _node_id(args)
    choice = args.choice

    if not choice:
        print("Error: --choice is required", file=sys.stderr)
        sys.exit(1)

    # Generate slug from choice label
    slug = re.sub(r'[^a-z0-9]+', '_', choice.lower()).strip('_')
    new_id = f"{node}_{slug}"

    # Load and update edges.json
    edges_path = os.path.join(tree, "edges.json")
    with open(edges_path, encoding="utf-8") as f:
        edges = json.load(f)

    if new_id in edges:
        print(f"Error: node '{new_id}' already exists in edges.json", file=sys.stderr)
        sys.exit(1)

    edges[new_id] = {"parent": node, "via_choice": choice}

    with open(edges_path, "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Gather parent world_state flags for the arc_note scaffold
    resolver = PathResolver(tree)
    parent_stream = list(resolver.emit_stream(node))
    world_flags = {}
    for rec in parent_stream:
        if rec.get("type") == "world_state":
            flags = rec.get("flags", {})
            world_flags.update(flags)

    flags_summary = ", ".join(f"{k}:{v}" for k, v in world_flags.items()) if world_flags else "none"

    # Scaffold the new node JSONL
    node_path = os.path.join(tree, "nodes", f"{new_id}.jsonl")
    records = [
        {"type": "scene", "id": f"s_{slug}_001",
         "content": f"[Scene continues from {node}. Player chose: {choice}]",
         "tags": []},
        {"type": "arc_note", "id": f"a_{slug}_001",
         "content": f"Branching from {node}. Player chose: {choice}. Honor world state: {flags_summary}",
         "author": "narrative_agent",
         "tags": ["continuity"]},
    ]

    with open(node_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Created node {new_id}. JSONL scaffold ready at {node_path}")

    # Suggest setting CURRENT_NODE
    print(f"Set CURRENT_NODE={new_id} to continue from this branch.")


def cmd_search(args):
    tree = _tree_root(args)
    grep_exprs = args.grep or []
    view = args.view or "transposed"

    if not grep_exprs:
        print("Error: --grep is required for search", file=sys.stderr)
        sys.exit(1)

    # Load all nodes from edges.json
    edges_path = os.path.join(tree, "edges.json")
    with open(edges_path, encoding="utf-8") as f:
        edges = json.load(f)

    # Compile IR for every leaf (or just compile each node independently
    # and merge). For cross-tree search, we compile each node as a standalone
    # path and collect all IR blocks.
    all_ir = []
    pipeline = NarrativePipeline(tree)

    # Find all leaf nodes (nodes that are not parents of any other node)
    parents = {v.get("parent") for v in edges.values()}
    leaves = [nid for nid in edges if nid not in parents]

    # Compile each leaf path — this covers the entire tree
    seen_paths = set()
    for leaf in sorted(leaves):
        ir = pipeline.compile_ir(leaf)
        # Deduplicate blocks by their start_line + node combo
        for block in ir:
            key = (block.get("_node"), block.get("start_line"))
            if key not in seen_paths and block.get("searchable"):
                all_ir.append(block)
                seen_paths.add(key)

    if view == "transposed":
        output = render_transposed_view(all_ir, grep_exprs=grep_exprs)
    elif view == "adaptive":
        output = render_adaptive_view(all_ir, grep_exprs=grep_exprs)
    else:
        print(f"Error: search supports 'transposed' or 'adaptive' views", file=sys.stderr)
        sys.exit(1)

    print(output)


def cmd_inspect(args):
    tree = _tree_root(args)
    node = _node_id(args)

    resolver = PathResolver(tree)
    node_file = resolver._node_path(node)

    if not node_file.exists():
        print(f"Error: {node_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(node_file, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            print(f"{i:4d}: {line}", end="")


def main():
    parser = argparse.ArgumentParser(
        description="VCC-Narrative: narrative branch tree compiler")
    sub = parser.add_subparsers(dest="command")

    # recall
    p_recall = sub.add_parser("recall", help="Compile ancestor chain context")
    p_recall.add_argument("--node", help="Target node ID (or set CURRENT_NODE)")
    p_recall.add_argument("--tree", help="Tree root directory (default: $NARRATIVE_TREE_ROOT or ./tree)")
    p_recall.add_argument("--grep", action="append", help="Tag or substring filter (repeatable for AND)")
    p_recall.add_argument("--view", choices=["ui", "full", "brief", "adaptive", "transposed"],
                          help="Output view (default: adaptive)")

    # branch
    p_branch = sub.add_parser("branch", help="Create a new branch node")
    p_branch.add_argument("--node", help="Parent node ID (or set CURRENT_NODE)")
    p_branch.add_argument("--tree", help="Tree root directory")
    p_branch.add_argument("--choice", required=True, help="Choice label for the branch")

    # search
    p_search = sub.add_parser("search", help="Search across all tree nodes")
    p_search.add_argument("--tree", help="Tree root directory")
    p_search.add_argument("--grep", action="append", help="Tag or substring filter (repeatable for AND)")
    p_search.add_argument("--view", choices=["adaptive", "transposed"],
                          help="Output view (default: transposed)")

    # inspect
    p_inspect = sub.add_parser("inspect", help="Dump raw JSONL with line numbers")
    p_inspect.add_argument("--node", help="Node ID to inspect")
    p_inspect.add_argument("--tree", help="Tree root directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "recall": cmd_recall,
        "branch": cmd_branch,
        "search": cmd_search,
        "inspect": cmd_inspect,
    }

    try:
        commands[args.command](args)
    except NodeNotFoundError as e:
        node_id = str(e).strip("'\"")
        tree = _tree_root(args)
        edges_path = os.path.join(tree, "edges.json")
        try:
            with open(edges_path, encoding="utf-8") as f:
                available = sorted(json.load(f).keys())
        except (FileNotFoundError, json.JSONDecodeError):
            available = []
        print(f"Error: node '{node_id}' not found in {edges_path}", file=sys.stderr)
        if available:
            print(f"Available nodes: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)
    except NodeFileMissingError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except CycleDetectedError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
