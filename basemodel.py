import json
import os
import time
import uuid
import google.generativeai as genai

# =======================
# CONFIG
# =======================
# Replace with your real Gemini API key or set environment variable GEMINI_API_KEY
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAj50T8tohWn1YGlgQ0uzXIumcHgr6yXWI")
MODEL_NAME = "gemma-3n-e2b-it"
HISTORY_FILE = "chat_history.json"

# =======================
# HISTORY MANAGEMENT
# =======================
def _ensure_history_file():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"chats": {}}, f, ensure_ascii=False, indent=2)

def load_all_history():
    _ensure_history_file()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_new_chat(title="New Chat"):
    data = load_all_history()
    cid = str(uuid.uuid4())
    data["chats"][cid] = {"title": title, "messages": [], "created_at": time.time()}
    save_all_history(data)
    return cid

def rename_chat(chat_id, new_title):
    data = load_all_history()
    if chat_id in data["chats"]:
        data["chats"][chat_id]["title"] = new_title
        save_all_history(data)

def delete_chat(chat_id):
    data = load_all_history()
    if chat_id in data["chats"]:
        del data["chats"][chat_id]
        save_all_history(data)

def append_message(chat_id, role, content):
    data = load_all_history()
    if chat_id in data["chats"]:
        data["chats"][chat_id]["messages"].append({"role": role, "content": content})
        save_all_history(data)

# =======================
# GEMINI AI
# =======================
def init_model_safely():
    try:
        key = API_KEY or ""
        if key.strip() == "" or key == "YOUR_GEMINI_API_KEY":
            return None, "API key belum diisi. Set GEMINI_API_KEY env var atau edit basemodel.py."
        genai.configure(api_key=key)
        model = genai.GenerativeModel(MODEL_NAME)
        chat = model.start_chat()
        return chat, None
    except Exception as e:
        return None, str(e)

def start_chat_with_history(messages):
    try:
        key = API_KEY or ""
        if key.strip() == "" or key == "YOUR_GEMINI_API_KEY":
            return None, "API key belum diisi."
        genai.configure(api_key=key)
        model = genai.GenerativeModel(MODEL_NAME)
        hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages]
        chat = model.start_chat(history=hist)
        return chat, None
    except Exception as e:
        return None, str(e)

def clean_text(text: str) -> str:
    # strip asterisk/hash to keep output clean in the chat UI
    return text.replace("*", "").replace("#", "")