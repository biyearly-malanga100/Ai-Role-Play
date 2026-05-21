# app.py
from flask import Flask, request, jsonify, render_template_string
import threading
from config import SUMMARY_THRESHOLD
from memory_manager import load_history, save_json, HISTORY_FILE, append_to_history
from world_state import get_targeted_context, load_world_state, update_world_state, get_state_summary
from agent_pipeline import librarian_agent, generate_chat, run_sleep_cycle, load_prompts, save_prompts

app = Flask(__name__)

# Single-Page App Layout Dashboard (Tailwind UI)
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dynamic AI Simulation Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen flex flex-col font-sans">

    <header class="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between shadow-md">
        <div class="flex items-center space-x-3">
            <i class="fa-solid class= text-emerald-400 text-2xl fa-republican"></i>
            <h1 class="text-xl font-bold tracking-wide text-gray-100">RPG Memory Engine</h1>
        </div>
        <div id="status-bar" class="text-sm bg-gray-900 px-4 py-2 rounded-lg border border-gray-700 text-gray-300">
            Loading Live System Ledger Metrics...
        </div>
    </header>

    <main class="flex-1 flex overflow-hidden">
        
        <div class="w-64 bg-gray-800 border-r border-gray-700 flex flex-col p-4 space-y-2">
            <button onclick="switchTab('chat')" id="btn-tab-chat" class="tab-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg bg-emerald-600 text-white font-medium transition">
                <i class="fa-regular fa-comments w-5"></i> <span>Simulation Terminal</span>
            </button>
            <button onclick="switchTab('prompts')" id="btn-tab-prompts" class="tab-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-700 hover:text-gray-200 transition">
                <i class="fa-solid fa-sliders w-5"></i> <span>Prompt Engineering</span>
            </button>
            <button onclick="switchTab('world')" id="btn-tab-world" class="tab-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-700 hover:text-gray-200 transition">
                <i class="fa-solid fa-earth-mythology w-5"></i> <span>World Matrix Ledger</span>
            </button>
            <div class="pt-6 border-t border-gray-700 mt-auto">
                <button onclick="triggerSleepCycle()" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 px-4 rounded-lg transition text-sm flex items-center justify-center space-x-2 shadow">
                    <i class="fa-solid fa-moon"></i> <span>Force Sleep Cycle</span>
                </button>
            </div>
        </div>

        <div class="flex-1 flex flex-col bg-gray-900 p-6 overflow-y-auto">
            
            <div id="tab-chat" class="flex-1 flex flex-col space-y-4 max-w-4xl mx-auto w-full">
                <div id="chat-box" class="flex-1 bg-gray-800 border border-gray-700 rounded-xl p-4 overflow-y-auto space-y-4 shadow-inner min-h-[450px] max-h-[550px]"></div>
                
                <div class="flex items-center space-x-3 bg-gray-800 p-2 rounded-xl border border-gray-700 shadow-md">
                    <input type="text" id="user-input" placeholder="Interact with your generated simulation world..." class="flex-1 bg-transparent text-gray-100 placeholder-gray-500 focus:outline-none px-3 py-2 text-base" onkeydown="if(event.key === 'Enter') sendMessage()">
                    <button onclick="sendMessage()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2.5 rounded-lg transition shadow flex items-center space-x-2">
                        <span>Send</span> <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </div>
            </div>

            <div id="tab-prompts" class="hidden max-w-4xl mx-auto w-full space-y-6">
                <h2 class="text-xl font-bold border-b border-gray-700 pb-2 text-emerald-400">Core Directive & Rule Configurator</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold mb-2 text-gray-300">System Core Prompt Framework ({targeted_context} tag auto-injects data):</label>
                        <textarea id="prompt-system" rows="3" class="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 focus:ring-1 focus:ring-emerald-500 outline-none font-mono"></textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold mb-2 text-gray-300">Librarian Agent Selector Context Filter:</label>
                        <textarea id="prompt-librarian" rows="4" class="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 focus:ring-1 focus:ring-emerald-500 outline-none font-mono"></textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold mb-2 text-gray-300">Sleep Cycle Summarization Extractor Engine Rules:</label>
                        <textarea id="prompt-sleep" rows="8" class="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 focus:ring-1 focus:ring-emerald-500 outline-none font-mono"></textarea>
                    </div>
                    <button onclick="savePromptsToServer()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2 px-6 rounded-lg transition shadow">Save Configurations</button>
                </div>
            </div>

            <div id="tab-world" class="hidden max-w-4xl mx-auto w-full space-y-4">
                <h2 class="text-xl font-bold border-b border-gray-700 pb-2 text-emerald-400">Live JSON State Document Editor</h2>
                <p class="text-sm text-gray-400">Directly modify the contents of the memory grid below. Ensure standard formatting conventions are verified before saving changes.</p>
                <textarea id="world-json-editor" rows="20" class="w-full bg-gray-800 border border-gray-700 rounded-xl p-4 font-mono text-xs text-green-400 focus:ring-1 focus:ring-emerald-500 outline-none shadow-inner"></textarea>
                <button onclick="saveWorldJsonToServer()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2 px-6 rounded-lg transition shadow">Commit Ledger Modifications</button>
            </div>

        </div>
    </main>

    <script>
        let currentHistory = [];

        function switchTab(tabName) {
            document.getElementById('tab-chat').classList.add('hidden');
            document.getElementById('tab-prompts').classList.add('hidden');
            document.getElementById('tab-world').classList.add('hidden');
            
            document.getElementById('btn-tab-chat').className = "tab-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-700 transition";
            document.getElementById('btn-tab-prompts').className = "tab-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-700 transition";
            document.getElementById('btn-tab-world').className = "tab-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-700 transition";

            document.getElementById('tab-' + tabName).classList.remove('hidden');
            const activeBtn = document.getElementById('btn-tab-' + tabName);
            activeBtn.className = "tab-btn w-full flex items-center space-x-3 px-4 py-3 rounded-lg bg-emerald-600 text-white font-medium transition";
            
            if(tabName === 'world') loadWorldStateData();
            if(tabName === 'prompts') loadPromptTemplates();
        }

        async function updateMetricsBar() {
            const res = await axios.get('/api/metrics');
            document.getElementById('status-bar').innerText = res.data.summary;
        }

        async function loadChatLog() {
            const res = await axios.get('/api/history');
            currentHistory = res.data.history;
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML = '';
            
            currentHistory.forEach((msg, idx) => {
                const isUser = msg.role === 'user';
                const wrapper = document.createElement('div');
                wrapper.className = `flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1 group`;
                
                wrapper.innerHTML = `
                    <div class="text-xs text-gray-500 font-semibold px-2">${isUser ? 'User' : 'Simulator'}</div>
                    <div class="relative max-w-2xl bg-gray-700 border border-gray-600 rounded-xl px-4 py-3 shadow text-gray-100 text-sm">
                        <div id="msg-text-${idx}" class="whitespace-pre-wrap">${escapeHtml(msg.content)}</div>
                        <div id="msg-edit-area-${idx}" class="hidden mt-2">
                            <textarea id="edit-input-${idx}" rows="3" class="w-full bg-gray-800 text-white border border-gray-600 rounded p-2 font-sans text-sm focus:outline-none"></textarea>
                            <div class="mt-2 flex space-x-2 justify-end">
                                <button onclick="cancelEdit(${idx})" class="text-xs bg-gray-600 text-gray-200 px-2 py-1 rounded">Cancel</button>
                                <button onclick="submitEdit(${idx})" class="text-xs bg-emerald-600 text-white px-2 py-1 rounded font-bold">Save Change</button>
                            </div>
                        </div>
                        <button onclick="activateEditMode(${idx}, '${msg.role}')" class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-emerald-400 text-xs transition bg-gray-800 p-1 rounded border border-gray-600 shadow">
                            <i class="fa-regular fa-pen-to-square"></i> Edit
                        </button>
                    </div>
                `;
                chatBox.appendChild(wrapper);
            });
            chatBox.scrollTop = chatBox.scrollHeight;
            updateMetricsBar();
        }

        function activateEditMode(idx, role) {
            document.getElementById(`msg-text-${idx}`).classList.add('hidden');
            const editArea = document.getElementById(`msg-edit-area-${idx}`);
            editArea.classList.remove('hidden');
            document.getElementById(`edit-input-${idx}`).value = currentHistory[idx].content;
        }

        function cancelEdit(idx) {
            document.getElementById(`msg-text-${idx}`).classList.remove('hidden');
            document.getElementById(`msg-edit-area-${idx}`).classList.add('hidden');
        }

        async function submitEdit(idx) {
            const newContent = document.getElementById(`edit-input-${idx}`).value;
            await axios.post('/api/history/edit', { index: idx, content: newContent });
            loadChatLog();
        }

        async function sendMessage() {
            const inp = document.getElementById('user-input');
            const text = inp.value.trim();
            if(!text) return;
            inp.value = '';
            
            // Optimistic rendering for speed
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML += `<div class="flex flex-col items-end space-y-1"><div class="text-xs text-gray-500 font-semibold px-2">User</div><div class="bg-gray-700 border border-gray-600 rounded-xl px-4 py-3 shadow text-sm text-gray-100">${escapeHtml(text)}</div></div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            await axios.post('/api/chat', { message: text });
            loadChatLog();
        }

        async function loadPromptTemplates() {
            const res = await axios.get('/api/prompts');
            document.getElementById('prompt-system').value = res.data.system_prompt_template;
            document.getElementById('prompt-librarian').value = res.data.librarian_prompt;
            document.getElementById('prompt-sleep').value = res.data.sleep_cycle_prompt;
        }

        async function savePromptsToServer() {
            const payload = {
                system_prompt_template: document.getElementById('prompt-system').value,
                librarian_prompt: document.getElementById('prompt-librarian').value,
                sleep_cycle_prompt: document.getElementById('prompt-sleep').value
            };
            await axios.post('/api/prompts', payload);
            alert("Prompt configurations successfully synchronized with background model engines.");
        }

        async function loadWorldStateData() {
            const res = await axios.get('/api/world');
            document.getElementById('world-json-editor').value = JSON.stringify(res.data, null, 4);
        }

        async function saveWorldJsonToServer() {
            try {
                const updated = JSON.parse(document.getElementById('world-json-editor').value);
                await axios.post('/api/world', updated);
                alert("World state successfully updated.");
                updateMetricsBar();
            } catch(e) {
                alert("JSON structural invalidity detected. Check commas, blocks, and alignments.");
            }
        }

        async function triggerSleepCycle() {
            alert("Forcing asynchronous background sleep cycle run...");
            const res = await axios.post('/api/sleep');
            updateMetricsBar();
            if(res.data.success) alert("Memory framework successfully optimized and condensed.");
        }

        function escapeHtml(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        window.onload = () => { loadChatLog(); };
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({"history": load_history()})

@app.route('/api/history/edit', methods=['POST'])
def edit_history():
    data = request.json
    idx = data.get("index")
    new_content = data.get("content")
    
    history = load_history()
    if 0 <= idx < len(history):
        history[idx]["content"] = new_content
        save_json(HISTORY_FILE, history)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Index bounds mismatch"}), 400

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    return jsonify({"summary": get_state_summary()})

@app.route('/api/prompts', methods=['GET', 'POST'])
def handle_prompts():
    if request.method == 'POST':
        save_prompts(request.json)
        return jsonify({"success": True})
    return jsonify(load_prompts())

@app.route('/api/world', methods=['GET', 'POST'])
def handle_world():
    if request.method == 'POST':
        update_world_state(request.json)
        return jsonify({"success": True})
    return jsonify(load_world_state())

@app.route('/api/sleep', methods=['POST'])
def force_sleep():
    history = load_history()
    success = run_sleep_cycle(history)
    return jsonify({"success": success})

@app.route('/api/chat', methods=['POST'])
def handle_chat_turn():
    user_text = request.json.get("message", "").strip()
    if not user_text:
        return jsonify({"error": "Empty input"}), 400
    
    # Commit input to memory array
    append_to_history("user", user_text)
    history = load_history()
    recent_chat = [msg['content'] for msg in history[-5:]]
    
    # 1. Execute routing librarian matching
    relevant_entity_names = librarian_agent(user_text, recent_chat)
    targeted_context = get_targeted_context(relevant_entity_names)
    
    # 2. Frame customized system directive string
    prompts = load_prompts()
    sys_prompt = prompts["system_prompt_template"].format(targeted_context=targeted_context)
    
    messages = [{"role": "system", "content": sys_prompt}]
    messages.extend(history[-5:]) # Read exact context constraints up to 5 messages only
    
    # 3. Model query processing
    final_response = generate_chat(messages)
    append_to_history("assistant", final_response)
    
    # 4. Sequential threshold tracking execution check
    if len(history) % SUMMARY_THRESHOLD == 0:
        threading.Thread(target=run_sleep_cycle, args=(history,), daemon=True).start()
        
    return jsonify({"response": final_response})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)