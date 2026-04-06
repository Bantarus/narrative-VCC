（this readme is written by human）

# VCC-Narrative: View-oriented Conversation Compiler for Narrative Branch Trees

[English](README.md) | [简体中文](README_cn.md) | [日本語](README_jp.md)

A fork of [VCC](https://github.com/lllyasviel/VCC) ("View-oriented Conversation Compiler for Agent Trace Analysis" - [Paper](https://arxiv.org/abs/2603.29678)) repurposed for **narrative branch trees in games** — RPGs, visual novels, interactive fiction, or any genre with branching storylines.

The upstream VCC compiles Claude Code JSONL logs into structured, searchable views with stable cross-view line-number pointers. This fork replaces Claude Code conversation logs with custom narrative JSONL nodes, giving you lossless recall of branching story paths, NPC state, world flags, and narrative agent continuity memos.

The upstream compiler core (`skills/conversation-compiler/`) is untouched. All narrative-specific code lives in `narrative/`.

# Narrative Tree Structure

A narrative tree lives in a directory (default: `./tree`) with this layout:

```
tree/
├── edges.json          ← parent/child relationships between nodes
└── nodes/
    ├── act1_root.jsonl
    ├── act1_fork_a.jsonl
    ├── act1_fork_b.jsonl
    └── act1_fork_b_1.jsonl
```

`edges.json` defines the tree topology:

```json
{
  "act1_root":     { "parent": null },
  "act1_fork_a":   { "parent": "act1_root",   "via_choice": "Apologize" },
  "act1_fork_b":   { "parent": "act1_root",   "via_choice": "Threaten" },
  "act1_fork_b_1": { "parent": "act1_fork_b", "via_choice": "Flee" }
}
```

Each node is a `.jsonl` file where every line is one record. Supported record types:

| Type | Purpose |
|------|---------|
| `scene` | Scene-setting narrative text |
| `npc_dialogue` | NPC speech with speaker and disposition |
| `player_choice` | Decision point with options and chosen action |
| `consequence` | World reaction to a choice |
| `world_state` | Flag mutations and deltas |
| `arc_note` | Narrative agent continuity memo (rendered like VCC thinking blocks) |
| `branch_point` | Marks child edges from this node |

Example records:

```jsonl
{"type":"scene","id":"s001","content":"The tavern falls silent as you enter.","tags":["loc:crow_tavern","time:night","arc:act1"]}
{"type":"npc_dialogue","id":"d001","speaker":"Marcus","content":"You shouldn't be here.","disposition":"hostile","tags":["npc:marcus","arc:marcus_conflict"]}
{"type":"player_choice","id":"c001","prompt":"How do you respond?","options":["Apologize","Threaten","Leave"],"chosen":"Threaten","tags":["choice:confrontation"]}
{"type":"world_state","id":"w001","flags":{"marcus_disposition":"hostile","thieves_guild_rep":15},"delta":{"thieves_guild_rep":"+5","marcus_disposition":"neutral→hostile"}}
{"type":"arc_note","id":"a001","content":"Marcus was neutral in prologue. Disposition flip here.","author":"narrative_agent","tags":["npc:marcus","continuity"]}
```

Junk types (`_agent_heartbeat`, `_debug_trace`, `_scaffold`, `_llm_meta`) are silently dropped by the lexer.

# Install

## Narrative skills (this fork)

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/YOUR_USER/narrative-VCC.git
cd narrative-VCC
uv sync
```

To install the Claude Code skills, copy the skill folders into your project:

    Please help me install the skills from
    /path/to/narrative-VCC
    just follow the INSTALL.md

## Upstream VCC skills

The original VCC skills (`conversation-compiler`, `readchat`, `recall`, `searchchat`) are included and work unchanged. See the [upstream VCC repo](https://github.com/lllyasviel/VCC) for details.

# CLI Usage

```bash
# Recall ancestor chain context for a node
python cli.py recall --node act1_fork_b_1 --view full

# Recall with tag-based filtering
python cli.py recall --node act1_fork_b_1 --grep npc:marcus --view adaptive

# Recall continuity snapshot (arc_notes + world_state, the default)
python cli.py recall --node act1_fork_b_1

# Search across ALL nodes in the tree
python cli.py search --tree ./tree --grep continuity

# Create a new branch from a node
python cli.py branch --node act1_fork_b_1 --choice "Hide in shadows"

# Inspect raw JSONL with line numbers
python cli.py inspect --node act1_fork_b
```

Environment variables (overridable by CLI flags):
- `NARRATIVE_TREE_ROOT` — default `./tree`
- `CURRENT_NODE` — current node for recall/branch

## Tag Query Syntax

| Pattern | Matches |
|---------|---------|
| `npc:marcus` | Exact tag match |
| `arc:marcus_conflict` | Exact tag match |
| `choice:` | Prefix match (all choice tags) |
| `continuity` | Bare tag match |
| `tavern` | Substring match on content (VCC-compatible grep fallback) |

Multiple `--grep` flags compose with AND: `--grep npc:marcus --grep continuity` matches blocks tagged with both.

# Claude Code Skills

Three narrative-specific slash commands:

### `/narrative-recall [query]`

Compiles and displays the ancestor chain for the current node. Without a query, shows a lightweight continuity snapshot (arc_notes + world_state).

```
/narrative-recall                      # continuity snapshot
/narrative-recall npc:marcus           # all marcus-tagged blocks
/narrative-recall continuity           # all continuity memos
```

### `/narrative-branch [choice_label]`

Creates a new child node branching from the current node. Scaffolds a JSONL file with a scene block and an arc_note carrying forward world state.

```
/narrative-branch "Threaten Marcus"
```

### `/narrative-search [query]`

Searches across ALL nodes in the tree (not just the current path). Returns a transposed view sorted by depth.

```
/narrative-search npc:marcus
/narrative-search "marcus_disposition"
```

## Upstream VCC Usage

The original VCC skills (`/recall`, `/searchchat`, `/readchat`) still work for Claude Code conversation logs:

`/recall`

`/searchchat how did we handle the captcha in that browser listener system we discussed last time?`

`/readchat` is for advanced usage, see below.

# How It Works

## Narrative Pipeline

The narrative compiler extends VCC's pipeline without modifying it:

```
edges.json + nodes/*.jsonl
        │
        ▼
  PathResolver        ← walks edges.json from target to root, emits annotated stream
        │
        ▼
  NarrativeLexer      ← drops junk types, emits LexTokens
        │
        ▼
  NarrativeParser     ← converts LexTokens into VCC-compatible IR dicts
        │
        ▼
  VCC assign_lines    ← stable line numbers (upstream, untouched)
        │
        ▼
  VCC lower / emit    ← view rendering (upstream, untouched)
```

The parser produces IR nodes with the same structure VCC expects (`type`, `content`, `searchable`, `_sec`, `_blk`), so the entire downstream pipeline (line assignment, lowering, emission) works unchanged.

Views available:
- **Full** — lossless rendering of the entire ancestor chain
- **Brief** — truncated overview
- **Adaptive** — tag/grep-filtered, preserving conversation structure
- **Transposed** — flat list of matches sorted by depth, for cross-tree scanning

## Upstream VCC Pipeline

A Claude Code JSONL like this (you can find lots of these things in your `~/.claude/projects`):

```
{"type":"user","message":{"id":"msg_user1","content":"I have two pets.\nCan you write a P..."}}
{"type":"assistant","message":{"id":"msg_asst1","content":[{"type":"thinking","thinking":"The
user wants a pet tracking module.\nThey have a dog (Buddy) and a cat (Whiskers).\nLet me chec
k if there's an existing file first...
```

gets compiled into these views:

## UI View

This simulates what the user see in CC

```
[user]

I have two pets.
Can you write a Python module for tracking them?
One is a dog named Buddy and a cat named Whiskers.

[assistant]

Sure! Let me check if there's an existing file.

* Read "src/pets.py" (example.txt:18-20,23-25)

No existing file.
I'll create a module with Dog and Cat classes.

* Write "src/pets.py" (example.txt:40-63,66-68)

Created src/pets.py.
```

The pointers like `(example.txt:18-20,23-25)` can jump to the exact lines for full detail as below.

## Full View

The complete transcipt. Line numbers are assigned once and shared accross all views.

Lets say this is `example.txt`:

```
  1  [user]
  2
  3  I have two pets.
  4  Can you write a Python module for tracking them?
  5  One is a dog named Buddy and a cat named Whiskers.
  6
  7  ══════════════════════════════
  8  [assistant]
  9
 10  >>>thinking
 11  The user wants a pet tracking module.
 12  They have a dog (Buddy) and a cat (Whiskers).
 13  Let me check if there's an existing file first.
 14  <<<thinking
 15
 16  Sure! Let me check if there's an existing file.
 17
 18  >>>tool_call Read:tu01
 19  file_path: src/pets.py
 20  <<<tool_call
 21
 22  ══════════════════════════════
 23  [tool_error] Read:tu01
 24
 25  Error: file not found src/pets.py
 26
 27  ══════════════════════════════
 28  [assistant]
 29
 30  >>>thinking
 31  No existing file.
 32  I'll create Dog and Cat subclasses.
 33  The dog needs walk tracking.
 34  The cat needs nap tracking.
 35  <<<thinking
 36
 37  No existing file.
 38  I'll create a module with Dog and Cat classes.
 39
 40  >>>tool_call Write:tu02
 41  file_path: src/pets.py
 42  content: |
 43    class Pet:
 44        def __init__(self, name, species):
 45            self.name = name
 46            self.species = species
 47
 48    class Dog(Pet):
 49        def __init__(self, name):
 50            super().__init__(name, 'dog')
 51            self.walks = []
 52
 53        def log_walk(self, duration, distance):
 54            self.walks.append({'min': duration, 'km': distance})
 55
 56    class Cat(Pet):
 57        def __init__(self, name):
 58            super().__init__(name, 'cat')
 59            self.naps = []
 60
 61        def log_nap(self, duration, spot):
 62            self.naps.append({'min': duration, 'spot': spot})
 63  <<<tool_call
 64
 65  ══════════════════════════════
 66  [tool] Write:tu02
 67
 68  File written successfully.
 69
 70  ══════════════════════════════
 71  [assistant]
 72
 73  Created src/pets.py.
```

## Adaptive View `--grep dog`

The view can be adapted to search queries like `--grep dog`. Only blocks contaning a match are shown, but the conversation struture is preserved. Each block has a pointer back to the full view.

```
[user]

(example.txt:3-5)
  5: One is a dog named Buddy and a cat named Whiskers.

══════════════════════════════
[assistant]

>>>thinking
(example.txt:11-13)
  12: They have a dog (Buddy) and a cat (Whiskers).
<<<thinking

══════════════════════════════
[assistant]

>>>thinking
(example.txt:31-34)
  33: The dog needs walk tracking.
<<<thinking

>>>tool_call Write:tu02
(example.txt:41-62)
  50:           super().__init__(name, 'dog')
<<<tool_call
```

`Write:tu02` spans 22 lines of code (41–62), but only line 50 (`'dog'`) matched: the Cat class (56–62) is absent. The pointer `41-62` tells the agent where to read the full block.

## Transposed View `--grep dog`

Same matches, but as a flat list. Each entry is taged with what it is (user message, thinking, tool call, etc.) and where to find it in the full view:

```
(example.txt:3-5) [user]
  5: One is a dog named Buddy and a cat named Whiskers.

(example.txt:11-13) [thinking]
  12: They have a dog (Buddy) and a cat (Whiskers).

(example.txt:31-34) [thinking]
  33: The dog needs walk tracking.

(example.txt:41-62) [tool_call]
  50:           super().__init__(name, 'dog')
```

The adaptive view keeps conversation order so it is good for understanding context around a match. The transposed view is a flat list so it is good for scanning all matches at once. All pointers points into the full view.

# Q&A

### "Just another agent memory system?"

Nope. Memory systems store precomputed stuff like summaries, embeddings, graphs. Those structures and levels are usually static. And most of them are calling LLMs to do summarization etc...

VCC stores nothing. Views are dynamic. They are computed on the fly from the original JSONL, then thrown away after use. (We call this "projection".)

### "Okay isn't this just grep?"

No not at all. Grep gives you matching lines, but you cant tell if a match is the user talking, the agent thinking, a tool call, or a tool result. VCC has **block range pointers** and **block roles**. 

Some people may keep asking *"Okay, then what about splitting chat log into message files and using filesystem grep? What about structured grep? What about my XXXX database system?"* 

Lets say you jump from a adaptive view to the full view with some block line number, the surrounding context is right there. To get that from a file-per-message split, you need a tree to track hierarchy as a tree-like thing and then use a linked list to track temporal order, and you maintain both, and you even need to determine how many "temporal surrounding" things are really the correct surrounding context. By the time you finally finally make it work you basically reimplemented VCC..

### "Well but isn't this just pretty-print?"

They are very different. Pretty-print just reformats text. VCC is a real compiler with lex, parse, IR, lower, emit. Some examples of what it does:

* The lexer drops junk records like `queue-operation`, `progress`, `api_error` before parsing even starts
* The parser turns tool call parameters from escaped JSON blobs into readable block-indented text
* The parser also strips `digits→` prefixes from Read tool results to recover original source, and decodes base64 images to files
* At the IR stage, split assistant messages (same ID but multiple JSONL records because of compaction) get reassembled into single sections
* Lowering strips harness XML (`<system-reminder>`, `<ide_opened_file>`, etc), filters internal tools (`TodoWrite`, `ToolSearch`), cleans ANSI escape codes, and hides pure-markup user turns
* The emitter produces three views sharing one line-number coordinate system

the IR stage assign line numbers once to ensure that everything si consistent. After that, lowering can only select, truncate, or annotate. The line numbers cannot reorder or renumber. So cross-view pointers are always consistent.

# Cite

    @article{zhang2026vcc,
      title={View-oriented Conversation Compiler for Agent Trace Analysis},
      author={Lvmin Zhang and Maneesh Agrawala},
      year={2026},
      url={https://github.com/lllyasviel/VCC}
    }