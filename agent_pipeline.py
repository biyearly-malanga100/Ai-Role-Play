# agent_pipeline.py
import ollama
import json
from config import MAIN_MODEL, FAST_MODEL
from world_state import load_world_state, update_world_state, get_entity_keys

def generate_chat(messages, model=MAIN_MODEL):
    response = ollama.chat(model=model, messages=messages)
    return response['message']['content']

def librarian_agent(user_input, recent_chat):
    """Scans keys to fetch only what is actively mentioned."""
    known_entities = get_entity_keys()
    if not known_entities:
        return []
        
    prompt = f"""You are a librarian. Identify which Known Entities are relevant to the User Input.
Known Entities: {', '.join(known_entities)}
User Input: {user_input}
Output strictly pure JSON: {{"relevant": ["Name1", "Name2"]}}"""
    try:
        response = ollama.generate(model=FAST_MODEL, prompt=prompt, format="json")
        return json.loads(response['response']).get("relevant", [])
    except Exception:
        return []

def run_sleep_cycle(episodic_memory):
    """Processes recent chat history periodically to extract core world updates."""
    chat_log = "\n".join([f"{m['role']}: {m['content']}" for m in episodic_memory[-5:]])
    current_state = load_world_state()
    
    prompt = f"""You are the World Simulation Engine. Review the recent chat log and update the World JSON State.
CRITICAL FILTER: Be highly selective. Ignore minor actions, flavor text, and background scenery. 
ONLY save or update essential narrative elements like: Persons, Places, Times/Dates, Active Quests, and Imminent Dangers.

Rules:
1. Maintain total schema freedom to add nested objects under "player_status" or "entities".
2. Preserve existing data unless directly changed by recent events.

[CURRENT STATE]:
{json.dumps(current_state, indent=2)}

[RECENT CHAT]:
{chat_log}

Output the ENTIRE updated JSON state. No extra text allowed."""
    try:
        print("\n[BACKGROUND TASK] Running Sleep Cycle (Filtering & Extracting Core Lore)...")
        response = ollama.generate(model=MAIN_MODEL, prompt=prompt, format="json")
        new_state = json.loads(response['response'])
        
        if "player_status" in new_state and "entities" in new_state:
            update_world_state(new_state)
            print(f"[BACKGROUND TASK] World State Saved. Tracking: {list(new_state['entities'].keys())}")
    except Exception as e:
        print(f"[BACKGROUND TASK] Sleep Cycle Failed: {e}")