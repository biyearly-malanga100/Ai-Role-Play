# main_gui.py
import tkinter as tk
from tkinter import scrolledtext
import threading
from config import SUMMARY_THRESHOLD
from memory_manager import load_history, append_to_history
from world_state import get_targeted_context, get_state_summary
from agent_pipeline import librarian_agent, generate_chat, run_sleep_cycle

class AICompanionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic RPG Companion")
        self.root.geometry("850x650")
        
        self.status_bar = tk.Label(root, text=get_state_summary(), bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 10), bg="#e0e0e0")
        self.status_bar.pack(side=tk.TOP, fill=tk.X)
        
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 12))
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.user_input = tk.Entry(input_frame, font=("Arial", 14))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", self.handle_send)
        
        self.send_button = tk.Button(input_frame, text="Send", command=self.handle_send, font=("Arial", 12), bg="#008CBA", fg="white")
        self.send_button.pack(side=tk.RIGHT)
        
        self.load_initial_chat()

    def append_to_ui(self, sender, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        self.status_bar.config(text=get_state_summary())

    def load_initial_chat(self):
        history = load_history()
        for msg in history[-5:]: 
            sender = "User" if msg['role'] == "user" else "AI"
            self.append_to_ui(sender, msg['content'])

    def handle_send(self, event=None):
        user_text = self.user_input.get().strip()
        if not user_text: return
        
        self.user_input.delete(0, tk.END)
        self.append_to_ui("User", user_text)
        append_to_history("user", user_text)
        
        self.user_input.config(state='disabled')
        self.send_button.config(state='disabled')
        
        threading.Thread(target=self.agentic_loop, args=(user_text,), daemon=True).start()

    def agentic_loop(self, user_text):
        try:
            history = load_history()
            recent_chat = [msg['content'] for msg in history[-5:]]
            
            # 1. Librarian fetches key files
            relevant_entity_names = librarian_agent(user_text, recent_chat)
            targeted_context = get_targeted_context(relevant_entity_names)
            
            sys_prompt = f"You are an RPG simulator. Rely on this context to maintain continuity:\n{targeted_context}"

            messages = [{"role": "system", "content": sys_prompt}]
            messages.extend(history[-5:]) # Read chat history up to 5 messages only
            
            # 2. Text generation
            final_response = generate_chat(messages)
            
            # 3. Save and render
            append_to_history("assistant", final_response)
            self.root.after(0, self.append_to_ui, "AI", final_response)
            
            # 4. Sleep Cycle: Periodic conditional processing every 5 turns
            if len(history) % SUMMARY_THRESHOLD == 0:
                threading.Thread(target=run_sleep_cycle, args=(history,), daemon=True).start()

        except Exception as e:
            self.root.after(0, self.append_to_ui, "System", f"Error: {str(e)}")
            
        finally:
            self.root.after(0, lambda: self.user_input.config(state='normal'))
            self.root.after(0, lambda: self.send_button.config(state='normal'))

if __name__ == "__main__":
    root = tk.Tk()
    app = AICompanionGUI(root)
    root.mainloop()