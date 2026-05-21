# world_state.py
import json
from config import STATE_FILE
from memory_manager import load_json, save_json

# A true pristine blank slate.
DEFAULT_STATE = {
    "player_status": {
        "current_location": "Unknown",
        "inventory": [],
        "active_quests": []
    },
    "entities": {} # The AI can organically grow nested sub-objects here
}

def load_world_state():
    return load_json(STATE_FILE, DEFAULT_STATE)

def update_world_state(new_state_dict):
    save_json(STATE_FILE, new_state_dict)

def get_entity_keys():
    state = load_world_state()
    return list(state.get("entities", {}).keys())

def get_targeted_context(relevant_entity_names):
    """Gathers only the specific profiles requested by the Librarian."""
    state = load_world_state()
    player = state.get("player_status", {})
    
    context = "[PLAYER STATUS]\n"
    for k, v in player.items():
        context += f"- {k}: {v}\n"
    context += "\n"
    
    if relevant_entity_names:
        context += "[RELEVANT LORE & ENTITY FILES]\n"
        for name in relevant_entity_names:
            entity_data = state.get("entities", {}).get(name)
            if entity_data:
                context += f"--- {name} ---\n{json.dumps(entity_data, indent=2)}\n\n"
                
    return context

def get_state_summary():
    """Generates a dynamic high-level view for the console/GUI."""
    state = load_world_state()
    player = state.get("player_status", {})
    entities = state.get("entities", {})
    
    loc = player.get("current_location", "Unknown")
    inv = player.get("inventory", [])
    inv_str = ", ".join(inv) if isinstance(inv, list) else str(inv)
    
    summary = f"Location: {loc} | Inventory: [{inv_str}]"
    if entities:
        summary += f" | Known Concepts: {', '.join(list(entities.keys())[:4])}"
    return summary