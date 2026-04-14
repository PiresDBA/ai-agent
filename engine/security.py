from core.llm import ask
from core.json_utils import safe_json_load


def security_check(code: str):
    """
    Analisa código e detecta vulnerabilidades com LLM.
    """

    res = ask("security", f"""
Analise vulnerabilidades no código abaixo:

Verifique:
- SQL injection
- XSS
- RCE
- secrets expostos
- subprocess unsafe
- command injection

Responda APENAS em JSON:

{{
  "approved": true,
  "issues": [],
  "risk_score": 0.0
}}

Código:
{code}
""")

    try:
        data = safe_json_load(res)

        return {
            "safe": data.get("approved", False),
            "issues": data.get("issues", []),
            "risk_score": data.get("risk_score", 1.0),
            "raw": res
        }

    except Exception as e:
        print("❌ SECURITY PARSE ERROR")
        print("RAW RESPONSE:", res)
        print("ERROR:", str(e))

        return {
            "safe": False,
            "issues": ["parse_error"],
            "risk_score": 1.0,
            "error": str(e)
        }