#!/usr/bin/env python3
"""
Script de inicialização do Antigravity Agent System.
Inicia o servidor FastAPI com configurações otimizadas.
"""
import os
import sys

# Fix UTF-8 para terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import subprocess

# Garante que rodamos do diretório raiz do projeto
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# Cria diretórios necessários
for d in ["workspace", "data", "logs"]:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)


def check_ollama():
    """Verifica se Ollama está rodando."""
    import requests
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            print(f"✅ Ollama online — {len(models)} modelo(s): {', '.join(models[:3])}")
            return True
    except Exception:
        pass

    print("⚠️  ATENÇÃO: Ollama não está rodando!")
    print("   Inicie com: ollama serve")
    print("   E instale um modelo com: ollama pull llama3.2:3b")
    print()
    return False


def main():
    import uvicorn

    print("\n" + "="*60)
    print("  🐶 BULLDOG AI v2.2")
    print("="*60)
    print()

    ollama_ok = check_ollama()

    print()
    print(f"  🌐 Dashboard:  http://localhost:8888")
    print(f"  📚 API Docs:   http://localhost:8888/docs")
    print(f"  💚 Health:     http://localhost:8888/health")
    print()
    print("  Pressione Ctrl+C para parar o servidor")
    print("="*60 + "\n")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        # DIAMOND STABILITY: Monitora pastas de código e o arquivo principal
        reload_dirs=["api", "core", "engine", "agents", "tools", "dashboard", "."],
        log_level="info",
        access_log=True,
        timeout_keep_alive=600,
        timeout_graceful_shutdown=60,
        forwarded_allow_ips="*"
    )


if __name__ == "__main__":
    main()
