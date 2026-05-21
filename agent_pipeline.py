# agent_pipeline.py
import ollama
import json
import os
from config import MAIN_MODEL, FAST_MODEL
from world_state import load_world_state, update_world_state, get_entity_keys

PROMPTS_FILE = "config_prompts.json"
DEFAULT_PROMPTS = {
    "system_prompt_template": "You are an RPG simulator. Rely on this context to maintain continuity:\n{targeted_context}",
    "librarian_prompt": "You are a librarian. Identify which Known Entities are relevant to the User Input.\nKnown Entities: {entities_list}\nUser Input: {user_input}\nOutput strictly pure JSON: {{\"relevant\": [\"Name1\", \"Name2\"]}}",
    "sleep_cycle_prompt": "You are the World Simulation Engine. Review the recent chat log and update the World JSON State.\nCRITICAL FILTER: Be highly selective. Ignore minor actions, flavor text, and background scenery.\nONLY save or update essential narrative elements like: Persons, Places, Times/Dates, Active Quests, and Imminent Dangers.\n\nRules:\n1. Maintain total schema freedom to add nested objects under \"player_status\" or \"entities\".\n2. Preserve existing data unless directly changed by recent events.\n\n[CURRENT STATE]:\n{current_state}\n\n[RECENT CHAT]:\n{chat_log}\n\nOutput the ENTIRE updated JSON state. No extra text allowed."
}

def load_prompts():
    if not os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PROMPTS, f, indent=4)
        return DEFAULT_PROMPTS
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_prompts(prompts_dict):
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts_dict, f, indent=4)

def generate_chat(messages, model=MAIN_MODEL):
    response = ollama.chat(model=model, messages=messages)
    return response['message']['content']

def librarian_agent(user_input, recent_chat):
    known_entities = get_entity_keys()
    if not known_entities:
        return []
    
    prompts = load_prompts()
    prompt = prompts["librarian_prompt"].format(
        entities_list=", ".join(known_entities),
        user_input=user_input
    )
    try:
        response = ollama.generate(model=FAST_MODEL, prompt=prompt, format="json")
        return json.loads(response['response']).get("relevant", [])
    except Exception:
        return []

def run_sleep_cycle(episodic_memory):
    chat_log = "\n".join([f"{m['role']}: {m['content']}" for m in episodic_memory[-5:]])
    current_state = load_world_state()
    prompts = load_prompts()
    
    prompt = prompts["sleep_cycle_prompt"].format(
        current_state=json.dumps(current_state, indent=2),
        chat_log=chat_log
    )
    try:
        print("\n[BACKGROUND] Running User-Customized Sleep Cycle...")
        response = ollama.generate(model=MAIN_MODEL, prompt=prompt, format="json")
        new_state = json.loads(response['response'])
        
        if "player_status" in new_state and "entities" in new_state:
            update_world_state(new_state)
            print("[BACKGROUND] World state updated successfully.")
            return True
    except Exception as e:
        print(f"[BACKGROUND] Sleep Cycle Failed: {e}")
    return False