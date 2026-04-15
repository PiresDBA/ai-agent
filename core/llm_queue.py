import threading
import time

llm_lock = threading.Lock()

def with_llm_lock(fn, *args, **kwargs):
    with llm_lock:
        time.sleep(0.5)  # evita overload do ollama
        return fn(*args, **kwargs)