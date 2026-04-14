from core.llm import ask
import json
import re
from core.router import route


def orchestrate(task: str):

    decision = route(task)

    return {
        "route": decision.route,
        "confidence": float(decision.confidence)
    }

def extract_json(text: str):
    """
    Extrai JSON de respostas sujas de LLM (com markdown ou texto extra).
    """
    if not text:
        raise ValueError("Resposta vazia do LLM")

    text = text.strip()

    # remove markdown
    text = text.replace("```json", "").replace("```", "")

    # tenta capturar primeiro JSON válido
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Nenhum JSON encontrado no output: {text}")

    return json.loads(match.group())


def route(task):

    res = ask("orchestrator", f"""
Classifique o seguinte pedido:

A = GAME (Unreal / Unity / jogos)
B = SAAS (web apps, APIs, sistemas)
C = DEV (clone, refactor, automação, GitHub)

IMPORTANTE:
- Responda APENAS com JSON válido
- Não use markdown
- Não explique nada

Formato obrigatório:
{{
  "route": "A|B|C",
  "confidence": 0.0
}}

Task:
{task}
""")

    try:
        return extract_json(res)

    except Exception as e:
        print("❌ ORCHESTRATOR ERROR")
        print("RAW RESPONSE:", res)
        print("ERROR:", str(e))

        return {
            "route": "C",
            "confidence": 0.3
        }