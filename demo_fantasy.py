#!/usr/bin/env python3
"""Demo: populate a fantasy story tree and exercise the narrative-VCC pipeline.

Run:  python demo_fantasy.py
"""

import json
import os
import shutil
from pathlib import Path

TREE = Path("tree_demo")


def write_node(name: str, records: list[dict]):
    path = TREE / "nodes" / f"{name}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_tree():
    if TREE.exists():
        shutil.rmtree(TREE)
    (TREE / "nodes").mkdir(parents=True)

    # ── edges ──
    edges = {
        "prologue":               {"parent": None},
        "ch1_village":            {"parent": "prologue",          "via_choice": "Investigate the village"},
        "ch1_forest":             {"parent": "prologue",          "via_choice": "Follow the lights into the forest"},
        "ch1_village_help":       {"parent": "ch1_village",       "via_choice": "Help the blacksmith"},
        "ch1_village_tavern":     {"parent": "ch1_village",       "via_choice": "Eavesdrop in the tavern"},
        "ch1_forest_shrine":      {"parent": "ch1_forest",        "via_choice": "Approach the shrine"},
        "ch1_forest_flee":        {"parent": "ch1_forest",        "via_choice": "Run back to the road"},
        "ch2_dungeon":            {"parent": "ch1_village_help",  "via_choice": "Enter the mines"},
        "ch2_dungeon_fight":      {"parent": "ch2_dungeon",       "via_choice": "Fight the guardian"},
        "ch2_dungeon_negotiate":  {"parent": "ch2_dungeon",       "via_choice": "Negotiate passage"},
    }
    with open(TREE / "edges.json", "w") as f:
        json.dump(edges, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # ── PROLOGUE ──
    write_node("prologue", [
        {"type": "scene", "id": "s_pro_01",
         "content": "You wake on a rain-slick road, your memory a shattered mirror. A signpost points two ways: east toward smoke and chimney-light, west toward pale wisps drifting between ancient oaks.",
         "tags": ["loc:crossroads", "time:dawn", "arc:awakening"]},
        {"type": "_agent_heartbeat", "ts": "2026-01-15T06:00:00Z"},
        {"type": "world_state", "id": "w_pro_01",
         "flags": {"player_hp": 20, "gold": 0, "reputation": 0, "has_weapon": False, "memory_fragments": 0},
         "delta": {}},
        {"type": "arc_note", "id": "a_pro_01",
         "content": "Player starts with amnesia. Memory fragments are the core progression mechanic. Each major NPC interaction can unlock one fragment. Track memory_fragments count — at 5, the endgame trigger fires.",
         "author": "narrative_agent",
         "tags": ["continuity", "arc:awakening", "mechanic:memory"]},
        {"type": "player_choice", "id": "c_pro_01",
         "prompt": "The rain is getting heavier. Which way?",
         "options": ["Investigate the village", "Follow the lights into the forest"],
         "chosen": None,
         "tags": ["choice:opening"]},
        {"type": "branch_point", "id": "bp_pro_01",
         "children": ["ch1_village", "ch1_forest"],
         "taken": None},
    ])

    # ── CH1: VILLAGE PATH ──
    write_node("ch1_village", [
        {"type": "scene", "id": "s_vil_01",
         "content": "Ashwick is a mining village clinging to a hillside. Half the buildings are boarded up. A blacksmith hammers alone in the forge, and warm light spills from the Broken Crown tavern.",
         "tags": ["loc:ashwick", "time:morning", "arc:village"]},
        {"type": "_debug_trace", "msg": "scene_loaded"},
        {"type": "npc_dialogue", "id": "d_vil_01",
         "speaker": "Elara", "disposition": "wary",
         "content": "Another drifter. The mines took the last group of adventurers three days ago. You don't look like you're here to help.",
         "tags": ["npc:elara", "arc:village", "loc:ashwick"]},
        {"type": "consequence", "id": "r_vil_01",
         "content": "A flash of recognition — Elara's face triggers a half-formed memory. You've been here before.",
         "tags": ["npc:elara", "mechanic:memory"]},
        {"type": "world_state", "id": "w_vil_01",
         "flags": {"memory_fragments": 1, "elara_met": True, "player_location": "ashwick"},
         "delta": {"memory_fragments": "0→1", "player_location": "crossroads→ashwick"}},
        {"type": "arc_note", "id": "a_vil_01",
         "content": "First memory fragment unlocked by seeing Elara. Player has been to Ashwick before — this is foreshadowing for the reveal that the player caused the mine collapse. Do NOT reveal this yet.",
         "author": "narrative_agent",
         "tags": ["npc:elara", "continuity", "mechanic:memory", "arc:village"]},
        {"type": "player_choice", "id": "c_vil_01",
         "prompt": "Elara turns back to the forge. The tavern hums with low voices.",
         "options": ["Help the blacksmith", "Eavesdrop in the tavern"],
         "chosen": None,
         "tags": ["choice:village_action"]},
        {"type": "branch_point", "id": "bp_vil_01",
         "children": ["ch1_village_help", "ch1_village_tavern"],
         "taken": None},
    ])

    # ── CH1: VILLAGE → HELP BLACKSMITH ──
    write_node("ch1_village_help", [
        {"type": "scene", "id": "s_help_01",
         "content": "You pick up a hammer without asking. Elara watches you shape the metal — your hands remember the rhythm even if your mind doesn't.",
         "tags": ["loc:ashwick", "npc:elara", "arc:village"]},
        {"type": "npc_dialogue", "id": "d_help_01",
         "speaker": "Elara", "disposition": "warming",
         "content": "You've done this before. Who are you?",
         "tags": ["npc:elara", "arc:village"]},
        {"type": "npc_dialogue", "id": "d_help_02",
         "speaker": "Elara", "disposition": "concerned",
         "content": "The mines have been sealed since the collapse. Something down there is still alive, though. We hear it at night — scraping, like claws on stone.",
         "tags": ["npc:elara", "arc:mines", "loc:ashwick"]},
        {"type": "consequence", "id": "r_help_01",
         "content": "Elara gives you a short sword and a lantern. 'If you're going down there, you'll need these.'",
         "tags": ["npc:elara", "item:short_sword", "item:lantern"]},
        {"type": "world_state", "id": "w_help_01",
         "flags": {"has_weapon": True, "has_lantern": True, "elara_disposition": "warming", "memory_fragments": 2},
         "delta": {"has_weapon": "false→true", "has_lantern": "false→true", "elara_disposition": "wary→warming", "memory_fragments": "1→2"}},
        {"type": "_agent_heartbeat", "ts": "2026-01-15T06:30:00Z"},
        {"type": "arc_note", "id": "a_help_01",
         "content": "Second memory fragment: muscle memory at the forge. Elara is warming to the player. She's given equipment. If player enters mines, Elara may follow later if disposition reaches 'trusting'. Track elara_disposition carefully.",
         "author": "narrative_agent",
         "tags": ["npc:elara", "continuity", "mechanic:memory", "arc:mines"]},
        {"type": "player_choice", "id": "c_help_01",
         "prompt": "The mine entrance is a dark maw in the hillside. Elara watches from the forge.",
         "options": ["Enter the mines", "Ask Elara about the collapse first"],
         "chosen": None,
         "tags": ["choice:mines_entry"]},
        {"type": "branch_point", "id": "bp_help_01",
         "children": ["ch2_dungeon"],
         "taken": None},
    ])

    # ── CH1: VILLAGE → TAVERN ──
    write_node("ch1_village_tavern", [
        {"type": "scene", "id": "s_tav_01",
         "content": "The Broken Crown is half-empty. A hooded figure in the corner nurses a drink. Two miners argue at the bar about whether the sealed mine entrance has been scratched open from the inside.",
         "tags": ["loc:broken_crown", "arc:village"]},
        {"type": "npc_dialogue", "id": "d_tav_01",
         "speaker": "Hooded Figure", "disposition": "cryptic",
         "content": "You don't remember, do you? That's probably for the best.",
         "tags": ["npc:stranger", "arc:awakening", "mechanic:memory"]},
        {"type": "_scaffold", "template": "tavern_ambient_v1"},
        {"type": "consequence", "id": "r_tav_01",
         "content": "The stranger slides a crumpled note across the table before vanishing into the rain. It reads: 'THE COLLAPSE WAS NOT AN ACCIDENT. CHECK THE FOREMAN'S OFFICE. —K'",
         "tags": ["item:note", "npc:stranger", "arc:mines"]},
        {"type": "world_state", "id": "w_tav_01",
         "flags": {"has_note": True, "stranger_met": True, "memory_fragments": 1, "knows_mine_secret": True},
         "delta": {"has_note": "false→true", "knows_mine_secret": "false→true"}},
        {"type": "arc_note", "id": "a_tav_01",
         "content": "The hooded stranger knows the player's past. This is 'K' — Kael, the former mine foreman. He survived the collapse and has been hiding. The note is a critical clue. If the player reaches the foreman's office in the mines, they'll find evidence that the player themselves triggered the collapse while under magical influence.",
         "author": "narrative_agent",
         "tags": ["npc:stranger", "npc:kael", "continuity", "arc:mines", "arc:awakening"]},
    ])

    # ── CH1: FOREST PATH ──
    write_node("ch1_forest", [
        {"type": "scene", "id": "s_for_01",
         "content": "The wisps lead you deeper. The oaks grow impossibly tall, their canopy blotting out the sky. You find a clearing with a stone shrine covered in glowing runes.",
         "tags": ["loc:elderwood", "time:morning", "arc:forest"]},
        {"type": "npc_dialogue", "id": "d_for_01",
         "speaker": "Voice from the Shrine", "disposition": "ancient",
         "content": "You return at last, vessel. The binding frays. Will you mend it, or let what sleeps beneath finally wake?",
         "tags": ["npc:shrine_spirit", "arc:forest", "arc:awakening"]},
        {"type": "_llm_meta", "model": "narrative-v3", "temp": 0.8},
        {"type": "consequence", "id": "r_for_01",
         "content": "A searing pain behind your eyes. A cascade of images: you, younger, pressing your hand to this very shrine. A bargain struck. A price unpaid.",
         "tags": ["mechanic:memory", "arc:awakening", "arc:forest"]},
        {"type": "world_state", "id": "w_for_01",
         "flags": {"memory_fragments": 2, "shrine_visited": True, "binding_status": "fraying", "player_location": "elderwood"},
         "delta": {"memory_fragments": "0→2", "shrine_visited": "false→true", "player_location": "crossroads→elderwood"}},
        {"type": "arc_note", "id": "a_for_01",
         "content": "Forest path gives 2 memory fragments at once (more direct supernatural contact). The shrine spirit recognizes the player as the original binder. The 'binding' holds a powerful entity beneath the mines — this connects both paths. If binding_status reaches 'broken', endgame triggers regardless of memory_fragments count.",
         "author": "narrative_agent",
         "tags": ["continuity", "arc:forest", "arc:awakening", "mechanic:memory", "mechanic:binding"]},
        {"type": "player_choice", "id": "c_for_01",
         "prompt": "The runes pulse. The voice waits.",
         "options": ["Approach the shrine", "Run back to the road"],
         "chosen": None,
         "tags": ["choice:shrine"]},
        {"type": "branch_point", "id": "bp_for_01",
         "children": ["ch1_forest_shrine", "ch1_forest_flee"],
         "taken": None},
    ])

    # ── CH1: FOREST → SHRINE ──
    write_node("ch1_forest_shrine", [
        {"type": "scene", "id": "s_shr_01",
         "content": "You press your palm to the stone. Light erupts. The runes burn themselves into your skin. When the light fades, you can see threads of magic woven through the trees — a vast net, fraying at the edges.",
         "tags": ["loc:elderwood", "arc:forest", "mechanic:binding"]},
        {"type": "npc_dialogue", "id": "d_shr_01",
         "speaker": "Shrine Spirit", "disposition": "relieved",
         "content": "The vessel remembers. But memory alone will not hold the binding. You need the anchor — it lies in the deep places, where the miners broke through.",
         "tags": ["npc:shrine_spirit", "arc:forest", "arc:mines"]},
        {"type": "world_state", "id": "w_shr_01",
         "flags": {"memory_fragments": 3, "has_runesight": True, "binding_status": "stabilizing", "knows_anchor_location": True},
         "delta": {"memory_fragments": "2→3", "has_runesight": "false→true", "binding_status": "fraying→stabilizing"}},
        {"type": "arc_note", "id": "a_shr_01",
         "content": "Player gained runesight (can see magical threads) and stabilized the binding temporarily. The anchor is in the mines — connecting forest path to village path. Player now has 3 fragments. The shrine spirit pointed to the mines, creating narrative convergence. All paths eventually lead underground.",
         "author": "narrative_agent",
         "tags": ["continuity", "arc:forest", "arc:mines", "mechanic:memory", "mechanic:binding"]},
    ])

    # ── CH1: FOREST → FLEE ──
    write_node("ch1_forest_flee", [
        {"type": "scene", "id": "s_flee_01",
         "content": "You stumble back through the trees. The wisps wink out one by one, as if disappointed. By the time you reach the road, the shrine clearing is gone — the forest has closed behind you.",
         "tags": ["loc:crossroads", "arc:forest"]},
        {"type": "consequence", "id": "r_flee_01",
         "content": "A dull ache behind your eyes. The memories that almost surfaced sink back into darkness. You're left with only a feeling: you were supposed to do something there.",
         "tags": ["mechanic:memory", "arc:awakening"]},
        {"type": "world_state", "id": "w_flee_01",
         "flags": {"memory_fragments": 1, "shrine_refused": True, "binding_status": "fraying", "player_location": "crossroads"},
         "delta": {"memory_fragments": "2→1", "shrine_refused": "true", "player_location": "elderwood→crossroads"}},
        {"type": "arc_note", "id": "a_flee_01",
         "content": "Player LOST a memory fragment by refusing the shrine (2→1). This is a penalty for retreating from supernatural contact. The forest path is now closed. Player must go to the village. If shrine_refused is true and player later reaches the mines, the binding will be weaker and the guardian encounter harder.",
         "author": "narrative_agent",
         "tags": ["continuity", "arc:forest", "mechanic:memory", "mechanic:binding"]},
    ])

    # ── CH2: DUNGEON ──
    write_node("ch2_dungeon", [
        {"type": "scene", "id": "s_dun_01",
         "content": "The mine swallows you. Elara's lantern throws wild shadows across collapsed timbers and rusted cart tracks. The air smells of sulfur and something older — ozone, like before a lightning strike.",
         "tags": ["loc:mines", "arc:mines", "time:underground"]},
        {"type": "npc_dialogue", "id": "d_dun_01",
         "speaker": "Elara", "disposition": "nervous",
         "content": "The main shaft collapsed here. But look — someone's been digging. These marks are fresh.",
         "tags": ["npc:elara", "arc:mines", "loc:mines"]},
        {"type": "scene", "id": "s_dun_02",
         "content": "Deeper. The walls begin to glow with the same runes you saw — or dreamed of — at the crossroads. A massive stone door blocks the path, carved with a warning in a language you shouldn't know but can read: 'WHAT IS BOUND HERE MUST NOT WAKE.'",
         "tags": ["loc:mines_deep", "arc:mines", "mechanic:binding"]},
        {"type": "npc_dialogue", "id": "d_dun_02",
         "speaker": "Guardian", "disposition": "territorial",
         "content": "The door groans open. A figure of living stone steps forward, runes blazing across its body. 'The binder returns. But you are diminished. Prove your worth or turn back.'",
         "tags": ["npc:guardian", "arc:mines", "mechanic:binding"]},
        {"type": "_agent_heartbeat", "ts": "2026-01-15T07:00:00Z"},
        {"type": "world_state", "id": "w_dun_01",
         "flags": {"player_location": "mines_deep", "guardian_encountered": True},
         "delta": {"player_location": "ashwick→mines_deep", "guardian_encountered": "false→true"}},
        {"type": "arc_note", "id": "a_dun_01",
         "content": "The guardian recognizes the player as 'the binder'. This confirms the player created the binding in their past life. The guardian's difficulty should scale: if has_runesight=true, the player can see the guardian's weak points (easier fight / better negotiation). If shrine_refused=true, the guardian is more aggressive. Check world state flags before resolving the encounter.",
         "author": "narrative_agent",
         "tags": ["npc:guardian", "continuity", "arc:mines", "mechanic:binding"]},
        {"type": "player_choice", "id": "c_dun_01",
         "prompt": "The guardian blocks the way. Its stone fist cracks the floor.",
         "options": ["Fight the guardian", "Negotiate passage"],
         "chosen": None,
         "tags": ["choice:guardian"]},
        {"type": "branch_point", "id": "bp_dun_01",
         "children": ["ch2_dungeon_fight", "ch2_dungeon_negotiate"],
         "taken": None},
    ])

    # ── CH2: DUNGEON → FIGHT ──
    write_node("ch2_dungeon_fight", [
        {"type": "scene", "id": "s_fight_01",
         "content": "You draw Elara's sword. The guardian charges. Stone meets steel in a shower of sparks. Each blow you land cracks its runes — and with each crack, a memory floods back.",
         "tags": ["loc:mines_deep", "arc:mines", "mechanic:binding"]},
        {"type": "consequence", "id": "r_fight_01",
         "content": "The guardian crumbles. In its dying light, you see it all: you were the court mage. You created the binding to seal an entity of pure hunger. The collapse — that was you too, trying to strengthen the seal. But something went wrong.",
         "tags": ["mechanic:memory", "arc:awakening", "arc:mines"]},
        {"type": "world_state", "id": "w_fight_01",
         "flags": {"guardian_defeated": True, "memory_fragments": 4, "player_hp": 8, "binding_status": "damaged", "knows_identity": True},
         "delta": {"guardian_defeated": "false→true", "memory_fragments": "2→4", "player_hp": "20→8", "binding_status": "stabilizing→damaged"}},
        {"type": "arc_note", "id": "a_fight_01",
         "content": "Fighting the guardian damaged the binding further (stabilizing→damaged). Player gained 2 memory fragments (now 4, one short of endgame trigger). Player now knows their identity as the court mage. Fighting cost HP (20→8). The entity below is closer to waking. Next node must escalate urgency — the seal is failing.",
         "author": "narrative_agent",
         "tags": ["npc:guardian", "continuity", "arc:mines", "mechanic:memory", "mechanic:binding"]},
    ])

    # ── CH2: DUNGEON → NEGOTIATE ──
    write_node("ch2_dungeon_negotiate", [
        {"type": "scene", "id": "s_neg_01",
         "content": "You raise your hands. 'I am the binder. I don't remember everything, but I know this seal matters.' The guardian pauses. Its runes dim from combat-red to a cautious amber.",
         "tags": ["loc:mines_deep", "arc:mines", "mechanic:binding"]},
        {"type": "npc_dialogue", "id": "d_neg_01",
         "speaker": "Guardian", "disposition": "testing",
         "content": "Words are wind in these halls. But the binding recognizes you, even if you do not recognize yourself. I will grant passage — if you swear to restore what you broke.",
         "tags": ["npc:guardian", "arc:mines", "mechanic:binding"]},
        {"type": "consequence", "id": "r_neg_01",
         "content": "The guardian steps aside. As you pass, it places a stone hand on your shoulder. A flood of ordered memories: the ritual, the seal, the court, the king who ordered it. You remember.",
         "tags": ["mechanic:memory", "arc:awakening", "arc:mines"]},
        {"type": "world_state", "id": "w_neg_01",
         "flags": {"guardian_allied": True, "memory_fragments": 5, "binding_status": "stabilizing", "knows_identity": True, "guardian_oath": True},
         "delta": {"guardian_allied": "false→true", "memory_fragments": "2→5", "guardian_oath": "false→true"}},
        {"type": "arc_note", "id": "a_neg_01",
         "content": "Negotiation preserved the binding (stays stabilizing) and gave the guardian as an ally. Player gained 3 memory fragments (now 5) — ENDGAME TRIGGER REACHED. The guardian's oath means it will help in the final confrontation. This is the 'golden path' — full memory, intact binding, guardian ally. Next node must handle the endgame: the entity below begins to stir, and the player must choose how to reseal it.",
         "author": "narrative_agent",
         "tags": ["npc:guardian", "continuity", "arc:mines", "mechanic:memory", "mechanic:binding", "endgame"]},
    ])

    print(f"Built tree at {TREE}/ with {len(edges)} nodes.")
    return edges


def run_tests():
    from subprocess import run
    import sys

    py = sys.executable
    tree = str(TREE)

    tests = [
        ("Recall: full ancestor chain for ch2_dungeon_fight",
         [py, "cli.py", "recall", "--node", "ch2_dungeon_fight", "--tree", tree, "--view", "full"]),

        ("Recall: continuity snapshot (default adaptive) for ch2_dungeon_negotiate",
         [py, "cli.py", "recall", "--node", "ch2_dungeon_negotiate", "--tree", tree]),

        ("Recall: grep npc:elara across village path",
         [py, "cli.py", "recall", "--node", "ch1_village_help", "--tree", tree, "--grep", "npc:elara", "--view", "adaptive"]),

        ("Recall: grep mechanic:binding across forest shrine path",
         [py, "cli.py", "recall", "--node", "ch1_forest_shrine", "--tree", tree, "--grep", "mechanic:binding"]),

        ("Search: all continuity notes across entire tree",
         [py, "cli.py", "search", "--tree", tree, "--grep", "continuity"]),

        ("Search: all mentions of the guardian",
         [py, "cli.py", "search", "--tree", tree, "--grep", "npc:guardian"]),

        ("Search: substring 'binding' across all nodes",
         [py, "cli.py", "search", "--tree", tree, "--grep", "binding"]),

        ("Inspect: raw JSONL for ch2_dungeon",
         [py, "cli.py", "inspect", "--node", "ch2_dungeon", "--tree", tree]),

        ("Branch: create new node from dungeon fight",
         [py, "cli.py", "branch", "--node", "ch2_dungeon_fight", "--tree", tree, "--choice", "Seal the entity with blood"]),
    ]

    for label, cmd in tests:
        print(f"\n{'='*70}")
        print(f"TEST: {label}")
        print(f"CMD:  {' '.join(cmd[1:])}")
        print(f"{'='*70}\n")
        result = run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"[stderr] {result.stderr}")


if __name__ == "__main__":
    build_tree()
    run_tests()
