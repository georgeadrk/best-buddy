import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import basemodel
import tts_gui

# ========= State =========
current_chat_id = None
chat_session = None
theme_mode = "dark"  # default dark

# ========= Theme =========
THEMES = {
    "dark": {
        "bg": "#0f172a",         # main background (slate-900)
        "panel": "#111827",      # panels (neutral-900)
        "panel_alt": "#1f2937",  # secondary panel
        "text": "#e5e7eb",       # text (gray-200)
        "muted": "#9ca3af",      # muted text
        "accent": "#22c55e",     # green accent
        "user_bubble": "#374151",# user message bg
        "bot_bubble": "#0b4e2a", # bot message bg (dark greenish)
        "entry_bg": "#111827",
        "entry_fg": "#e5e7eb",
        "border": "#334155",
        "btn_bg": "#1f2937",
        "btn_fg": "#e5e7eb",
    },
    "light": {
        "bg": "#f5f7fb",
        "panel": "#ffffff",
        "panel_alt": "#f3f4f6",
        "text": "#111827",
        "muted": "#4b5563",
        "accent": "#16a34a",
        "user_bubble": "#e5e7eb",
        "bot_bubble": "#dcfce7",
        "entry_bg": "#ffffff",
        "entry_fg": "#111827",
        "border": "#d1d5db",
        "btn_bg": "#f3f4f6",
        "btn_fg": "#111827",
    },
}

def apply_theme():
    th = THEMES[theme_mode]
    root.configure(bg=th["bg"])

    # Frames
    top_bar.configure(bg=th["panel"])
    sidebar_frame.configure(bg=th["panel"])
    main_frame.configure(bg=th["panel"])
    input_frame.configure(bg=th["panel"])

    # Labels
    title_label.configure(bg=th["panel"], fg=th["text"])
    history_label.configure(bg=th["panel"], fg=th["text"])

    # Buttons
    for b in (new_btn, rename_btn, delete_btn, send_btn, tts_btn, theme_btn):
        b.configure(bg=th["btn_bg"], fg=th["btn_fg"], activebackground=th["panel_alt"], activeforeground=th["text"], bd=0, relief="flat")

    # Sidebar listbox
    sidebar.configure(bg=th["panel_alt"], fg=th["text"], selectbackground=th["accent"], selectforeground="#ffffff", bd=0, highlightthickness=1, highlightbackground=th["border"])
    sidebar_scroll.configure(bg=th["panel"], troughcolor=th["panel"], highlightthickness=0, bd=0)

    # Chat area
    chat_area.configure(bg=th["panel_alt"], fg=th["text"], bd=0, highlightthickness=1, highlightbackground=th["border"])
    chat_scroll.configure(bg=th["panel"], troughcolor=th["panel"], highlightthickness=0, bd=0)

    # Entry (single-line)
    input_entry.configure(bg=th["entry_bg"], fg=th["entry_fg"], insertbackground=th["entry_fg"], bd=1, highlightthickness=1, highlightbackground=th["border"])

    # Tags for chat bubbles
    chat_area.tag_configure("user", background=th["user_bubble"], foreground=th["text"], lmargin1=10, lmargin2=10, rmargin=60, spacing3=6, wrap="word")
    chat_area.tag_configure("bot", background=th["bot_bubble"], foreground=th["text"], lmargin1=60, lmargin2=60, rmargin=10, spacing3=6, wrap="word")
    chat_area.tag_configure("sys", foreground=th["muted"])

def toggle_theme():
    global theme_mode
    theme_mode = "light" if theme_mode == "dark" else "dark"
    theme_btn.configure(text=f"{'Dark' if theme_mode == 'light' else 'Light'} Mode")
    apply_theme()

# ========= Sidebar / History =========
def refresh_sidebar():
    sidebar.delete(0, tk.END)
    data = basemodel.load_all_history()
    # sort by created_at desc
    items = sorted(data["chats"].items(), key=lambda kv: kv[1].get("created_at", 0), reverse=True)
    for cid, info in items:
        sidebar.insert(tk.END, f"{info['title']}  |  {cid}")

def get_selected_chat_id_from_sidebar():
    sel = sidebar.curselection()
    if not sel:
        return None
    val = sidebar.get(sel[0])
    if " | " in val:
        return val.split(" | ")[-1].strip()
    return None

def on_sidebar_select(event=None):
    cid = get_selected_chat_id_from_sidebar()
    if not cid:
        return
    load_chat(cid)

def new_chat():
    global current_chat_id, chat_session
    current_chat_id = basemodel.add_new_chat("New Chat")
    chat_session, err = basemodel.init_model_safely()
    if err:
        messagebox.showerror("API Key / Model Error", err)
        return
    clear_chat()
    append_sys("🆕 New chat created.")
    refresh_sidebar()
    # auto-select newly created chat
    select_chat_in_sidebar(current_chat_id)

def rename_chat():
    cid = get_selected_chat_id_from_sidebar() or current_chat_id
    if not cid:
        messagebox.showinfo("Info", "Select a chat to rename.")
        return
    data = basemodel.load_all_history()
    old_title = data["chats"][cid]["title"]
    new_title = simpledialog.askstring("Rename Chat", "New title:", initialvalue=old_title)
    if new_title:
        basemodel.rename_chat(cid, new_title.strip())
        refresh_sidebar()
        select_chat_in_sidebar(cid)

def delete_chat():
    cid = get_selected_chat_id_from_sidebar() or current_chat_id
    if not cid:
        messagebox.showinfo("Info", "Select a chat to delete.")
        return
    data = basemodel.load_all_history()
    title = data["chats"].get(cid, {}).get("title", cid)
    if messagebox.askyesno("Delete Chat", f"Delete chat '{title}'?"):
        basemodel.delete_chat(cid)
        if cid == current_chat_id:
            clear_chat()
        refresh_sidebar()

def select_chat_in_sidebar(cid):
    # find item and select it
    for i in range(sidebar.size()):
        val = sidebar.get(i)
        if val.endswith(cid):
            sidebar.selection_clear(0, tk.END)
            sidebar.selection_set(i)
            sidebar.see(i)
            break

def load_chat(chat_id):
    global current_chat_id, chat_session
    current_chat_id = chat_id
    data = basemodel.load_all_history()
    info = data["chats"].get(chat_id)
    if not info:
        return
    messages = info["messages"]

    clear_chat()
    for m in messages:
        if m["role"] == "user":
            append_user(m["content"])
        else:
            append_bot(m["content"])
    chat_session, err = basemodel.start_chat_with_history(messages)
    if err:
        messagebox.showerror("Model Error", err)

# ========= Chat Display Helpers =========
def clear_chat():
    chat_area.config(state=tk.NORMAL)
    chat_area.delete("1.0", tk.END)
    chat_area.config(state=tk.DISABLED)

def append_sys(text):
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, text + "\n", "sys")
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)

def append_user(text):
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, text + "\n", "user")
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)

def append_bot(text):
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, text + "\n", "bot")
    chat_area.see(tk.END)
    chat_area.config(state=tk.DISABLED)

# ========= Sending / AI =========
def ensure_chat_ready():
    global chat_session, current_chat_id
    if not current_chat_id:
        current_chat_id = basemodel.add_new_chat("New Chat")
        refresh_sidebar()
        select_chat_in_sidebar(current_chat_id)
    if not chat_session:
        chat_session, err = basemodel.init_model_safely()
        if err:
            messagebox.showerror("API Key / Model Error", err)
            return False
    return True

def send_message(event=None):
    if not ensure_chat_ready():
        return "break"
    user_text = input_entry.get().strip()
    if not user_text:
        return "break"

    # Auto-rename "New Chat" using first line of first user message
    data = basemodel.load_all_history()
    if data["chats"][current_chat_id]["title"] == "New Chat":
        first_line = user_text.split("\n")[0].strip()
        title = (first_line[:30] + "…") if len(first_line) > 30 else first_line
        if title:
            basemodel.rename_chat(current_chat_id, title)
            refresh_sidebar()
            select_chat_in_sidebar(current_chat_id)

    basemodel.append_message(current_chat_id, "user", user_text)
    append_user(user_text)
    input_entry.delete(0, tk.END)

    def do_ai():
        global chat_session
        try:
            resp = chat_session.send_message(user_text)
            ai_text = basemodel.clean_text(getattr(resp, "text", str(resp)))
            basemodel.append_message(current_chat_id, "ai", ai_text)
            append_bot(ai_text)
            tts_gui.speak(ai_text)   # interrupting, persistent TTS
        except Exception as e:
            messagebox.showerror("AI Error", str(e))

    # Schedule without blocking UI
    root.after(10, do_ai)
    return "break"

def toggle_tts():
    state = tts_gui.toggle_tts()
    tts_btn.configure(text=f"TTS: {'ON' if state else 'OFF'}")

# ========= UI =========
root = tk.Tk()
root.title("ChatGPT-like AI (Gemma) with TTS")
root.geometry("1040x680")

# Top Bar
top_bar = tk.Frame(root, height=44)
top_bar.pack(fill=tk.X, side=tk.TOP)
title_label = tk.Label(top_bar, text="George AI (Gemma)", font=("Segoe UI", 12, "bold"))
title_label.pack(side=tk.LEFT, padx=10, pady=8)

tts_btn = tk.Button(top_bar, text="TTS: ON", command=toggle_tts)
tts_btn.pack(side=tk.RIGHT, padx=8, pady=6)

theme_btn = tk.Button(top_bar, text="Light Mode", command=toggle_theme)
theme_btn.pack(side=tk.RIGHT, padx=8, pady=6)

# Sidebar
sidebar_frame = tk.Frame(root, width=260)
sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
history_label = tk.Label(sidebar_frame, text="Chats", font=("Segoe UI", 10, "bold"))
history_label.pack(anchor="w", padx=10, pady=(10, 4))

btns_row = tk.Frame(sidebar_frame)
btns_row.pack(fill=tk.X, padx=10, pady=(0, 6))
new_btn = tk.Button(btns_row, text="New", command=new_chat)
rename_btn = tk.Button(btns_row, text="Rename", command=rename_chat)
delete_btn = tk.Button(btns_row, text="Delete", command=delete_chat)
new_btn.pack(side=tk.LEFT, padx=(0, 6))
rename_btn.pack(side=tk.LEFT, padx=(0, 6))
delete_btn.pack(side=tk.LEFT)

sidebar_holder = tk.Frame(sidebar_frame)
sidebar_holder.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
sidebar = tk.Listbox(sidebar_holder, activestyle="dotbox")
sidebar_scroll = tk.Scrollbar(sidebar_holder, orient="vertical", command=sidebar.yview)
sidebar.configure(yscrollcommand=sidebar_scroll.set)
sidebar.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
sidebar_scroll.pack(side=tk.RIGHT, fill=tk.Y)
sidebar.bind("<<ListboxSelect>>", on_sidebar_select)

# Main panel
main_frame = tk.Frame(root)
main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Chat display
chat_holder = tk.Frame(main_frame)
chat_holder.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 6))

chat_area = tk.Text(chat_holder, state=tk.DISABLED, wrap="word", font=("Segoe UI", 10))
chat_scroll = tk.Scrollbar(chat_holder, orient="vertical", command=chat_area.yview)
chat_area.configure(yscrollcommand=chat_scroll.set)
chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# Input area (single-line Entry + Send)
input_frame = tk.Frame(main_frame)
input_frame.pack(fill=tk.X, padx=10, pady=(0, 12))

input_entry = tk.Entry(input_frame, font=("Segoe UI", 10))
input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
input_entry.bind("<Return>", send_message)     # Enter to send
# Optional: Shift+Enter to insert newline in Entry is not standard; keeping single-line behavior.

send_btn = tk.Button(input_frame, text="Send", command=send_message)
send_btn.pack(side=tk.RIGHT)

# Apply theme & load sidebar
apply_theme()
refresh_sidebar()

# Start with a new chat so it's instantly usable!
new_chat()

root.mainloop()