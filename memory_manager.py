# memory_manager.py
import json
import os
from config import HISTORY_FILE, GRAPH_FILE

def load_json(filepath, default_data):
    if not os.path.exists(filepath):
        save_json(filepath, default_data)
        return default_data
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default_data

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- Episodic Memory (Raw Chat History) ---
def load_history():
    return load_json(HISTORY_FILE, [])

def append_to_history(role, content):
    history = load_history()
    history.append({"role": role, "content": content})
    save_json(HISTORY_FILE, history)

# --- Memory Graph (Relational Triplets) ---
def load_graph():
    return load_json(GRAPH_FILE, [])

def add_triplet(subject, relation, obj):
    graph = load_graph()
    new_triplet = [subject, relation, obj]
    if new_triplet not in graph:
        graph.append(new_triplet)
        save_json(GRAPH_FILE, graph)

def get_relevant_facts(user_input):
    graph = load_graph()
    keywords = user_input.lower().split()
    relevant = []
    for triplet in graph:
        if any(k in triplet[0].lower() or k in triplet[2].lower() for k in keywords):
            relevant.append(f"({triplet[0]}) -[{triplet[1]}]-> ({triplet[2]})")
    return "\n".join(relevant) if relevant else "No specific historical facts found."