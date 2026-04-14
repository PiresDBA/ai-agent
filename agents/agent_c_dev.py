from core.llm import ask
from tools.github_fetcher import search

def agent_c(task):

    repos = search(task)

    return ask("dev_agent", f"""
Você é um engenheiro de software.

Escolha o melhor repositório e adapte.

Repositórios:
{repos}

Objetivo:
{task}

Aplique:
- refactor
- melhorias
- correções
""")