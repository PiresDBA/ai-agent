import json
import os

MEM_FILE = "memory.json"


def load_memory():
    if not os.path.exists(MEM_FILE):
        return {}
    with open(MEM_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(data):
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def remember(key, value):
    mem = load_memory()
    mem[key] = value
    save_memory(mem)


def recall(key):
    mem = load_memory()
    return mem.get(key)