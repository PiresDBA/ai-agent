from core.llm import ask

def quality_check(code):

    res = ask("quality", f"""
Avalie arquitetura:

- performance
- organização
- escalabilidade
- boas práticas

Retorne JSON:
{{
  "score": 0-1,
  "issues": [],
  "improvements": []
}}

Código:
{code}
""")

    import json
from core.json_utils import safe_json_load

def quality_check(res):
    try:
        if not res:
            return {"ok": False, "error": "empty response"}

        return safe_json_load(res)

    except Exception as e:
        print("❌ QUALITY ERROR:", res)
        return {"ok": False, "error": str(e)}