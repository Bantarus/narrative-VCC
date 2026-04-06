# Installation Guide for Agents (Manual Install)

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (for dependency management)

## Install

### Narrative skills (new)

Clone this repo to any temporary location. Then:

1. Run `uv sync` in the cloned repo to install dependencies.
2. Copy the three narrative skill folders (`narrative-recall`, `narrative-branch`, `narrative-search`) from `skills/` into your project's `.claude/skills/`.
3. Copy the `narrative/` directory and `cli.py` into your project root (or keep them in the cloned repo and reference via path).
4. Create a `tree/` directory in your project with `edges.json` and `nodes/` to hold your narrative data.

### Upstream VCC skills

Copy the four original folders inside `skills/` (`conversation-compiler`, `readchat`, `recall`, `searchchat`) into your project's `.claude/skills/`.

### All-in-one

To install everything (narrative + upstream VCC):

Copy all seven folders from `skills/` (`conversation-compiler`, `readchat`, `recall`, `searchchat`, `narrative-recall`, `narrative-branch`, `narrative-search`) into your project's `.claude/skills/`.

## Update

Clone this repo to any temporary location. Delete the skill folders from your `.claude/skills/`, then copy the new versions from the cloned `skills/` into `.claude/skills/`. Also update `narrative/` and `cli.py` if present.

## Verify

After install or update, ask the user to restart Claude Code, then:

- Run `/recall` to test upstream VCC skills work.
- Run `/narrative-recall` (with `CURRENT_NODE` set) to test narrative skills work.
- Run `python cli.py recall --node act1_root --tree ./tree` to test the CLI.

## Uninstall

Delete the skill folders from your `.claude/skills/`. Remove `narrative/`, `cli.py`, and `tree/` if no longer needed. Ask the user to restart Claude Code.
