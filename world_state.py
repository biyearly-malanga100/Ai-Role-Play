# world_state.py
import json
from config import STATE_FILE
from memory_manager import load_json, save_json

DEFAULT_STATE = {
    "player_status": {
        "current_location": "Unknown",
        "inventory": [],
        "active_quests": []
    },
    "entities": {}
}

def load_world_state():
    return load_json(STATE_FILE, DEFAULT_STATE)

def update_world_state(new_state_dict):
    save_json(STATE_FILE, new_state_dict)

def get_entity_keys():
    state = load_world_state()
    return list(state.get("entities", {}).keys())

def get_targeted_context(relevant_entity_names):
    """
    Returns ONLY what was requested.
    Always includes a tiny player status block (location + quests only — no full inventory dump).
    Entity details are only added for the specific names passed in.
    """
    state = load_world_state()
    player = state.get("player_status", {})

    # Lean player block — just the essentials
    context = "[PLAYER STATUS]\n"
    context += f"- Location: {player.get('current_location', 'Unknown')}\n"
    quests = player.get("active_quests", [])
    if quests:
        context += f"- Active Quests: {', '.join(quests) if isinstance(quests, list) else quests}\n"

    # World conditions (if present) — affects NPC behavior
    conditions = state.get("world_conditions", {})
    if conditions:
        context += "\n[WORLD CONDITIONS]\n"
        for k, v in conditions.items():
            context += f"- {k}: {v}\n"

    # Specific entity facts (only if requested by librarian)
    if relevant_entity_names:
        context += "\n[RELEVANT LORE & ENTITY FILES]\n"
        for name in relevant_entity_names:
            entity_data = state.get("entities", {}).get(name)
            if entity_data:
                context += f"--- {name} ---\n{json.dumps(entity_data, indent=2)}\n\n"

    return context

def get_state_summary():
    """Short status bar string."""
    state = load_world_state()
    player = state.get("player_status", {})
    entities = state.get("entities", {})

    loc = player.get("current_location", "Unknown")
    inv = player.get("inventory", [])
    inv_str = ", ".join(inv) if isinstance(inv, list) and inv else "empty"

    summary = f"📍 {loc}  |  🎒 {inv_str}"
    if entities:
        keys = list(entities.keys())[:3]
        summary += f"  |  Known: {', '.join(keys)}"
    return summary