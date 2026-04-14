from core.llm import ask

def auto_fix(project, report):

    return ask("fixer", f"""
Corrija o projeto com base no relatório:

{report}

Aplique melhorias no código.
""")