import pyttsx3
import threading
import queue
import time

# Global state
tts_enabled = True
engine = pyttsx3.init()
engine.setProperty("rate", 185)

# Pick male-ish voice (or fallback to English)
try:
    voices = engine.getProperty("voices")
    chosen = None
    for v in voices:
        name = (v.name or "").lower()
        if "male" in name:  # heuristic for male
            chosen = v.id
            break
    if not chosen:  # fallback to English
        for v in voices:
            if "en" in (v.name or "").lower() or "en" in (v.id or "").lower():
                chosen = v.id
                break
    if chosen:
        engine.setProperty("voice", chosen)
except Exception:
    pass

# Queue for texts to speak
_text_queue = queue.Queue()
_stop_event = threading.Event()
_current_text = None

def toggle_tts():
    global tts_enabled
    tts_enabled = not tts_enabled
    return tts_enabled

def speak(text: str):
    if not text or not text.strip():
        return
    try:
        while not _text_queue.empty():  # clear old text for interrupt behavior
            _text_queue.get_nowait()
    except Exception:
        pass
    _text_queue.put(text)

def _tts_loop():
    engine.startLoop(False)  # Non-blocking loop
    while not _stop_event.is_set():
        engine.iterate()  # process internal events
        try:
            text = _text_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        if tts_enabled and text.strip():
            try:
                engine.stop()  # interrupt previous
                engine.say(text)
            except Exception as e:
                print("TTS error:", e)
        time.sleep(0.05)  # prevent CPU hogging

# Start thread once
threading.Thread(target=_tts_loop, daemon=True).start()