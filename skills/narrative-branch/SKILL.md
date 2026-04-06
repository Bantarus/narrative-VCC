---
name: narrative-branch
description: "Register a new child node branching from the current node. Use when: the user says /narrative-branch, or needs to create a new narrative branch from a player choice."
---

# narrative-branch

Register a new child node branching from the current node.

## Usage

```
/narrative-branch "Threaten Marcus"
/narrative-branch "Flee the tavern"
```

## Behavior

1. Read `CURRENT_NODE` from env — if unset, ask the user which node to branch from
2. Read `NARRATIVE_TREE_ROOT` from env (default: `./tree`)
3. Run:

```bash
python cli.py branch --node $CURRENT_NODE --choice "choice_label"
```

4. This will:
   - Generate a new `node_id`: `{current_node}_{slugified_choice_label}`
   - Add an entry to `tree/edges.json`: `{ "parent": CURRENT_NODE, "via_choice": "choice_label" }`
   - Scaffold a new `.jsonl` file in `tree/nodes/` with:
     - A `scene` block pre-populated from the parent's `branch_point` context
     - An `arc_note` block templated with: "Branching from {parent}. Player chose: {choice_label}. Honor world state: {summary of parent's world_state flags}"
5. Set `CURRENT_NODE` = new node_id
6. Confirm: "Created node {new_id}. JSONL scaffold ready at tree/nodes/{new_id}.jsonl"

## Rules

- The new node's JSONL scaffold is a starting point — the narrative agent should extend it
- Always honor the parent's `world_state` flags in downstream content
- The `arc_note` in the scaffold is a continuity memo, not narrative content
