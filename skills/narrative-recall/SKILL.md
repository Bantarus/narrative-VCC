---
name: narrative-recall
description: "Compile and display the ancestor chain context for a narrative node. Use when: the user says /narrative-recall, or needs to recall narrative context, continuity notes, or world state along a branch path."
---

# narrative-recall

Compile and display the ancestor chain context for a narrative node.

## Usage

```
/narrative-recall                        # all arc_note + world_state blocks (minimum continuity context)
/narrative-recall npc:marcus             # all marcus-tagged blocks from root to current node
/narrative-recall arc:marcus_conflict    # full arc trace
/narrative-recall continuity             # all continuity constraint memos
```

## Behavior

1. Read `NARRATIVE_TREE_ROOT` from env (default: `./tree`)
2. Read `CURRENT_NODE` from env — if unset, ask the user which node to recall
3. Run the narrative pipeline:

```bash
python cli.py recall --node $CURRENT_NODE --grep "$query" --view adaptive
```

4. Display the adaptive view with source-node labels
5. If no query is provided, default to showing `arc_note` and `world_state` blocks for a lightweight continuity snapshot

## Query Syntax

| Pattern | Matches |
|---------|---------|
| `npc:marcus` | All blocks tagged `npc:marcus` |
| `arc:marcus_conflict` | All blocks in that arc |
| `choice:` | All player_choice blocks |
| `continuity` | All arc_note blocks tagged `continuity` |
| `tavern` | Substring match on content (VCC-compatible grep fallback) |

Multiple `--grep` flags compose with AND (blocks must match all expressions).

## Rules

- Never summarize ancestor content — this system provides lossless recall
- `arc_note` records are read-only memos from the narrative agent; display them but never edit
- Cross-view line pointers must remain stable
