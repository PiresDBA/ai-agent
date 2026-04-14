from core.llm import ask
import json

def decide(user):
    prompt = f"""
Analise:

{user}

Regras:
- Se contém URL → clone_site
- Se é app/jogo → github
- Se pergunta → search

Retorne JSON:

{{"type": "...", "strategy": "..."}}
"""
    res = ask("manager_agent", prompt)

    try:
        return json.loads(res)
    except:
        return {"type": "search", "strategy": "github"}