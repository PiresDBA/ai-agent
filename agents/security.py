from core.llm import ask

def security_agent(code):
    return ask("security", f"""
Analise segurança do código:

- SQL injection
- XSS
- RCE
- secrets expostos

Retorne:
- risk_score
- issues
- fixes

Código:
{code}
""")