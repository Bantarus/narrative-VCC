---
name: narrative-search
description: "Search across ALL nodes in the narrative tree (not just the current path). Use when: the user says /narrative-search, or needs to find narrative content, tags, or world state across the entire tree."
---

# narrative-search

Search across ALL nodes in the narrative tree, not just the current ancestor path.

## Usage

```
/narrative-search npc:marcus
/narrative-search continuity
/narrative-search "marcus_disposition"
```

## Behavior

1. Read `NARRATIVE_TREE_ROOT` from env (default: `./tree`)
2. Run:

```bash
python cli.py search --tree $NARRATIVE_TREE_ROOT --grep "$query" --view transposed
```

3. Return transposed view across all nodes, each result tagged with its source `node_id`
4. Results are sorted by node depth (shallow ancestors first) then by occurrence order

## Query Syntax

| Pattern | Matches |
|---------|---------|
| `npc:marcus` | All blocks tagged `npc:marcus` across all nodes |
| `continuity` | All continuity-tagged arc_notes across all nodes |
| `"some text"` | Substring match on content across all nodes |

Multiple `--grep` flags compose with AND.

## Rules

- This searches the entire tree, not a single path — useful for finding divergent branches
- Results include the source node_id so you can trace which branch contains the match
- No summarization — raw content only
