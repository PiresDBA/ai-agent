from core.llm import ask
import json
import subprocess

import subprocess

def git_sync(message="auto sync"):
    try:
        subprocess.run(["git", "add", "."], check=True)

        commit = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True
        )

        if "nothing to commit" in commit.stdout.lower():
            print("⚠️ Nada para commit")
            return

        subprocess.run(["git", "push"], check=True)

        print("✅ Git sync OK")

    except Exception as e:
        print("❌ Git error:", e)
        
def decide(user):
    prompt = f"""
Analise o pedido do usuário:

"{user}"

Classifique corretamente:

type:
- game
- web_app
- clone_site
- automation
- search

strategy:
- github
- clone
- build
- research

REGRAS IMPORTANTES:
- Só use "clone_site" se houver uma URL clara (http/https)
- Para jogos ou apps, prefira "github"
- Para perguntas, use "search"

Responda SOMENTE JSON válido, sem explicações.
NUNCA use markdown.
NUNCA use texto extra.
NUNCA use explicações.
Se não souber, responda:
{"type":"search","strategy":"research"}
Exemplo:
{{"type": "game", "strategy": "github"}}
"""

    res = ask("manager_agent", prompt)

    try:
        return json.loads(res)
    except Exception:
        print("⚠️ Erro interpretando decisão do LLM:", res)

    # fallback seguro
    return {
        "type": "search",
        "strategy": "research"
    }