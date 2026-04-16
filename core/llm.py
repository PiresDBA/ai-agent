"""
LLM Core — Integração robusta com Ollama.
- Detecta modelos instalados automaticamente
- Fallback automático entre modelos
- Timeout controlado por chamada
- Logging detalhado
"""
import requests
import subprocess
import time
import threading
import os
from functools import lru_cache

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"

# Lock global para serializar chamadas ao Ollama (uma GPU, uma requisição por vez)
_ollama_lock = threading.Lock()

# Catálogo de modelos Cloud conhecidos (mesmo que não instalados localmente)
CLOUD_CATALOG = [
    "minimax-m2:cloud",
    "minimax-m2.1:cloud",
    "minimax-m2.5:cloud",
    "minimax-m2.7:cloud",
    "kimi-k2.5:cloud",
    "glm-5:cloud",
    "gemma4:31b-cloud",
    "qwen3.5:397b-cloud",
    "gpt-oss:120b-cloud",
    "gpt-oss:20b-cloud"
]

# Modelos preferidos por tipo de tarefa (do mais leve ao mais pesado)
PREFERRED_MODELS = [
    "llama3.1:8b",
    "qwen2.5-coder:7b",
    "deepseek-coder:latest",
    "llama3.1:latest",
    "llama3.2:3b",
    "gemma3:4b",
    "mistral:latest",
    "phi3:latest",
] + CLOUD_CATALOG

def classify_model(model_name: str) -> str:
    """Classifica modelo como 'Diamond Local' ou 'Diamond Cloud'."""
    name = model_name.lower()
    if ":cloud" in name or "-cloud" in name or "minimax" in name or "gpt" in name or "claude" in name:
        return "Diamond Cloud"
    return "Diamond Local"


@lru_cache(maxsize=1)
def _get_available_models_cached() -> frozenset:
    """Detecta modelos instalados no Ollama via API (cache por sessão)."""
    for attempt in range(3):
        try:
            r = requests.get(OLLAMA_TAGS_URL, timeout=5)
            if r.status_code == 200:
                data = r.json()
                models = {m["name"] for m in data.get("models", [])}
                # print(f"✅ Ollama: {len(models)} modelo(s) disponível(is)")
                return frozenset(models)
        except Exception:
            if attempt < 2: time.sleep(1)
            continue

    # Fallback: tenta via CLI
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, timeout=10)
        models = set()
        for line in out.splitlines()[1:]:
            if line.strip():
                models.add(line.split()[0])
        return frozenset(models)
    except Exception:
        pass

    print("⚠️ Não foi possível listar modelos Ollama — usando todos como fallback")
    return frozenset()


def get_available_models() -> list[str]:
    """Retorna lista ordenada de modelos disponíveis."""
    available = _get_available_models_cached()
    if not available:
        return PREFERRED_MODELS  # assume todos disponíveis se não conseguir detectar

    # Ordena pelos preferidos primeiro, depois o resto
    ordered = [m for m in PREFERRED_MODELS if m in available]
    others = [m for m in available if m not in PREFERRED_MODELS]
    return ordered + sorted(others)


def invalidate_model_cache():
    """Limpa o cache de modelos (chama se adicionar novos modelos ao Ollama)."""
    _get_available_models_cached.cache_clear()


def get_chat_model(model_name: str = None, temperature: float = 0.3):
    """Retorna uma instância de ChatOllama compatível com LangChain."""
    from langchain_ollama import ChatOllama
    available = get_available_models()
    target = model_name if model_name in available else (available[0] if available else "llama3.2:3b")
    
    return ChatOllama(
        model=target,
        base_url="http://127.0.0.1:11434",
        temperature=temperature
    )


def get_crewai_llm(model_name: str = None):
    """Retorna a string de modelo no formato 'ollama/name' para o CrewAI."""
    available = get_available_models()
    target = model_name if model_name in available else (available[0] if available else "llama3.2:3b")
    return f"ollama/{target}"


def _call_ollama_raw(model: str, agent: str, prompt: str, timeout: int = 180) -> str:
    """
    Chamada HTTP direta ao Ollama. Thread-safe via lock global.
    Aplica o Contrato Global da Bulldogue automaticamente a todos os agentes, exceto o router.
    """
    
    # Injection of the Safe Operations Contract
    if agent != "router":
        try:
            contract_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CONTRATO.md")
            if os.path.exists(contract_path):
                with open(contract_path, "r", encoding="utf-8") as f:
                    contract = f.read()
                prompt += f"\n\n=== CONTRATO DE OPERAÇÃO OBRIGATÓRIO ===\n{contract}"
        except Exception:
            pass

    payload = {
        "model": model,
        "prompt": f"Você é {agent}.\n\n{prompt}",
        "stream": False,
        "options": {
            "temperature": 0.3,      # menos alucinação, mais consistência
            "num_predict": 4096,     # tokens máximos de resposta
            "top_p": 0.9,
        }
    }

    with _ollama_lock:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout or 600)

    response.raise_for_status()
    data = response.json()

    result = data.get("response", "").strip()
    if not result:
        raise ValueError("Ollama retornou resposta vazia")

    return result


def ask(agent: str, prompt: str, model: str = None, timeout: int = 600) -> str:
    """
    Interface principal para chamar LLMs via Ollama.
    
    Args:
        agent: Nome/papel do agente (ex: "game_agent", "fixer")
        prompt: Prompt para o modelo
        model: Modelo específico a usar (opcional, usa fallback automático)
        timeout: Timeout em segundos (padrão Diamond 600s)
    
    Returns:
        Resposta do modelo como string, ou "" em caso de falha total.
    """
    models_to_try = get_available_models()

    if model:
        # Coloca o modelo preferido na frente
        models_to_try = [model] + [m for m in models_to_try if m != model]

    last_error = None

    for m in models_to_try:
        msg = f"  ▶ [{agent}] → {m}"
        print(msg)
        try:
            with open("logs/llm.log", "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
                
            # Retentativa interna de conexão (Diamante) para lidar com picos de CPU
            for attempt in range(3):
                try:
                    result = _call_ollama_raw(m, agent, prompt, timeout)
                    msg_ok = f"  ✅ [{agent}] OK ({len(result)} chars)"
                    print(msg_ok)
                    with open("logs/llm.log", "a", encoding="utf-8") as f:
                        f.write(f"[{time.strftime('%H:%M:%S')}] {msg_ok}\n")
                    return result
                except requests.exceptions.ConnectionError:
                    if attempt == 2: raise
                    time.sleep(1)
        except Exception as e:
            last_error = str(e)
            if "Connection" in last_error or "11434" in last_error:
                print(f"  ⚠️ Conexão falhou com {m}, tentando próximo...")
            else:
                print(f"  ⏱ [{m}] Erro/Timeout — tentando próximo")
            continue

    print(f"  💀 [{agent}] Todos os modelos falharam. Último erro: {last_error}")
    return ""


def ask_with_system(agent: str, system_prompt: str, user_prompt: str,
                    model: str = None, timeout: int = 600) -> str:
    """
    Versão com system prompt separado (melhor para modelos que suportam).
    Combina system + user num único prompt para compatibilidade universal.
    """
    combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
    return ask(agent, combined, model=model, timeout=timeout)