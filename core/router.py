from core.llm import ask
from core.schemas import RouteDecision
from core.json_utils import safe_json_load


def build_prompt(user: str):
    return f"""
Você é um classificador de intenções.

Regras:
- Responda APENAS JSON válido
- Sem texto adicional
- Sem markdown

Classes:
A = GAME (Unreal, Unity, jogos)
B = SAAS (web apps, APIs, sistemas)
C = DEV (clone, automação, GitHub, refactor)

Formato obrigatório:
{{
  "route": "A|B|C",
  "confidence": 0.0
}}

Pedido:
{user}
""".strip()


def route(user: str, retries: int = 2):

    last_error = None
    raw = None

    for attempt in range(retries + 1):

        raw = ask("router", build_prompt(user))

        try:
            data = safe_json_load(raw)
            return RouteDecision.model_validate(data)

        except Exception as e:
            last_error = str(e)

    # fallback FINAL (controlado)
    print("❌ ROUTER FAILED AFTER RETRIES")
    print("LAST RAW:", raw)
    print("ERROR:", last_error)

    return RouteDecision(
        route="C",
        confidence=0.4
    )