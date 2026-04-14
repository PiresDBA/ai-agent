from core.llm import ask

def security_agent(code):

    return ask("security", f"""
Analise segurança:

- SQL injection
- XSS
- RCE
- secrets expostos

Retorne:
- risk_score
- issues
- fixes
- approved

Código:
{code}
""")