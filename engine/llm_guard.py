import requests
import threading
import time

ollama_lock = threading.Lock()

OLLAMA_URL = "http://localhost:11434/api/generate"

MODELS = [
    "llama3.2:3b",   # principal (leve e estável)
    "qwen3.5:4b"     # fallback
]

def call_ollama(agent, prompt, timeout=180):
    last_error = None

    for model in MODELS:

        for attempt in range(2):  # retry simples
            try:
                with ollama_lock:  # 🔥 fila global (BLINDAGEM REAL)

                    print(f"▶ LLM [{agent}] MODEL={model} ATTEMPT={attempt+1}")

                    response = requests.post(
                        OLLAMA_URL,
                        json={
                            "model": model,
                            "prompt": f"Você é {agent}\n{prompt}",
                            "stream": False
                        },
                        timeout=timeout
                    )

                response.raise_for_status()
                data = response.json()

                if "response" not in data or not data["response"]:
                    raise Exception("Empty response")

                return data["response"]

            except Exception as e:
                last_error = str(e)
                print(f"❌ LLM ERROR ({model}):", e)
                time.sleep(1)

    print("💀 LLM FAILED ALL MODELS:", last_error)
    return ""