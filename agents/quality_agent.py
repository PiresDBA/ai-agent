from core.llm import ask

def quality_agent(code):

    return ask("quality", f"""
Avalie qualidade de software:

- arquitetura
- performance
- boas práticas

Retorne:
- score 0-1
- problemas
- melhorias
""")