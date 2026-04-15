"""
Autofix — Solicita ao LLM correções para um projeto com problemas.
"""
from core.llm import ask


def auto_fix(project: str, report: str | dict) -> str:
    """
    Solicita ao LLM que corrija o projeto com base num relatório de problemas.

    Args:
        project: Código ou descrição do projeto atual
        report: Relatório de problemas (string ou dict)

    Returns:
        Código/projeto corrigido como string
    """
    report_str = str(report) if not isinstance(report, str) else report

    return ask("senior_fixer", f"""Você é um engenheiro de software sênior.

Corrija o projeto com base no relatório de problemas abaixo.

RELATÓRIO:
{report_str[:2000]}

PROJETO ATUAL:
{str(project)[:3000]}

REGRAS:
- Corrija a causa raiz, não apenas sintomas
- Garanta funcionamento no Windows
- Retorne o código final completo e funcional
- Sem placeholders ou TODOs""")