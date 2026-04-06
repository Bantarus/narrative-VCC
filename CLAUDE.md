# VCC-Narrative — Claude Code Project Instructions

This is a narrative branch tree compiler. You are acting as both the **narrative agent** and the **compiler operator** — you write story content into JSONL nodes and use the compiler to recall context.

## Tree Location

- Tree root: `./tree` (or `$NARRATIVE_TREE_ROOT`)
- Edges: `tree/edges.json`
- Nodes: `tree/nodes/<node_id>.jsonl`

## Workflow: Collaborative Storytelling

When the user wants to work on the story, follow this loop:

### 1. Orient — recall context before writing

Before writing ANY new content, always recall the ancestor chain for the current node:

```bash
python cli.py recall --node <CURRENT_NODE> --tree ./tree
```

This gives you the arc_notes and world_state you MUST honor. If you need full detail:

```bash
python cli.py recall --node <CURRENT_NODE> --tree ./tree --view full
```

### 2. Write — extend a node's JSONL

When the user describes what happens next in the story, translate their input into JSONL records appended to the current node file. Use the record types:

| Type | When to use |
|------|-------------|
| `scene` | Narrative description, setting, atmosphere |
| `npc_dialogue` | An NPC speaks (include `speaker`, `disposition`) |
| `player_choice` | Present the player with options (set `chosen` to null until resolved) |
| `consequence` | World reacts to a choice |
| `world_state` | Track flag changes (`flags` = current state, `delta` = what changed) |
| `arc_note` | Write a continuity memo for yourself — what must future nodes honor |
| `branch_point` | When a choice creates diverging paths (list `children` node IDs) |

**Always end a node with an `arc_note`** summarizing what future nodes must know.

Example — appending to a node:

```bash
cat >> tree/nodes/current_node.jsonl << 'JSONL'
{"type":"scene","id":"s_xxx_01","content":"The door creaks open.","tags":["loc:dungeon","arc:act2"]}
{"type":"npc_dialogue","id":"d_xxx_01","speaker":"Elara","content":"Stay close.","disposition":"protective","tags":["npc:elara"]}
{"type":"world_state","id":"w_xxx_01","flags":{"player_location":"inner_chamber"},"delta":{"player_location":"corridor→inner_chamber"}}
{"type":"arc_note","id":"a_xxx_01","content":"Elara is now protective. Player entered inner chamber. Honor elara_disposition:protective in downstream nodes.","author":"narrative_agent","tags":["continuity","npc:elara"]}
JSONL
```

### 3. Branch — when the story forks

When a player choice creates diverging paths:

1. Add a `player_choice` record with options and `"chosen": null`
2. Add a `branch_point` record listing child node IDs
3. Create child nodes:

```bash
python cli.py branch --node <CURRENT_NODE> --tree ./tree --choice "Choice label"
```

4. Then switch to the chosen branch and continue writing there

### 4. Search — find content across the tree

When you need to check what happened on other branches:

```bash
python cli.py search --tree ./tree --grep "npc:marcus"
python cli.py search --tree ./tree --grep "continuity"
```

## Rules — DO NOT VIOLATE

1. **Always recall before writing.** Never write new content without checking the ancestor chain's arc_notes and world_state first.
2. **Honor world state.** If `marcus_disposition:hostile` is set upstream, Marcus is hostile in all downstream nodes. No exceptions.
3. **No summarization.** This system provides lossless recall. Never summarize or compress narrative content.
4. **arc_notes are sacred.** They are continuity constraints. Read them, obey them, write new ones.
5. **IDs must be unique.** Use the pattern `{type_prefix}_{node_slug}_{sequence}` (e.g., `s_dungeon_03`).
6. **Tags are your index.** Always tag records with relevant `npc:`, `loc:`, `arc:`, `mechanic:`, `choice:` tags. This is how search works.
7. **Do not modify upstream nodes.** When extending the story, only append to the current leaf node or create new child nodes. Never edit records in ancestor nodes.
8. **Delta must be accurate.** In `world_state` records, `delta` shows what changed (`"old→new"`), `flags` shows the current state after the change.

## Conversation Patterns

**User says something like "what's happened so far?"**
→ Run `recall --view full` for the current node

**User says "what does [character] know?" or "where is [item]?"**
→ Run `search --grep npc:character` or `search --grep item:name`

**User says "I want to [action]" or describes what the player does**
→ Recall context, then write the appropriate JSONL records (scene, consequence, world_state, arc_note)

**User says "what are my choices?" or presents a decision point**
→ Write a `player_choice` record with options, then ask which they choose

**User picks a choice that creates a new branch**
→ Run `cli.py branch`, then recall the new node and continue writing there

**User says "what if I had chosen differently?"**
→ Recall the alternate branch: `recall --node <other_branch> --view full`

## Quick Reference

```bash
# Recall context (default: continuity snapshot)
python cli.py recall --node NODE --tree ./tree

# Recall full ancestor chain
python cli.py recall --node NODE --tree ./tree --view full

# Recall with tag filter
python cli.py recall --node NODE --tree ./tree --grep TAG --view adaptive

# Search entire tree
python cli.py search --tree ./tree --grep QUERY

# Create a branch
python cli.py branch --node NODE --tree ./tree --choice "LABEL"

# Inspect raw JSONL
python cli.py inspect --node NODE --tree ./tree
```
