from core.llm import ask

def agent_b(task):
    return ask("saas_agent", f"""
Crie um sistema SaaS completo.

Stack sugerida:
- FastAPI ou Node
- React frontend
- Auth + DB

Pedido:
{task}
""")