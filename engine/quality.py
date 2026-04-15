"""
Quality Check — Avaliação de qualidade do projeto gerado.
Usa LLM para analisar código e retornar score estruturado.
"""
from core.llm import ask
from core.json_utils import safe_json_load


def quality_check(code_or_output: str | dict) -> dict:
    """
    Avalia a qualidade do código/output gerado pelo agente.

    Args:
        code_or_output: Código fonte como string, ou dict com 'stdout'/'stderr'

    Returns:
        dict com: {score, issues, improvements, ok}
    """
    # Normaliza o input
    if isinstance(code_or_output, dict):
        content = code_or_output.get("stdout", "") or code_or_output.get("code", "")
        error_content = code_or_output.get("stderr", "") or code_or_output.get("error", "")

        if error_content:
            # Se há erro de execução, penaliza pesado
            return {
                "score": 0.1,
                "issues": [f"Erro de execução: {error_content[:300]}"],
                "improvements": ["Corrija os erros de execução antes de avaliar qualidade"],
                "ok": False
            }
        content = content or str(code_or_output)
    else:
        content = str(code_or_output)

    if not content or len(content.strip()) < 20:
        if isinstance(code_or_output, dict) and code_or_output.get("success"):
            content = "O código executou localmente com sucesso silencioso (típico de GUI/Pygame/Server)."
        else:
            return {
                "score": 0.0,
                "issues": ["Output vazio ou insuficiente"],
                "improvements": ["Gere código real funcional sem esconder saídas críticas."],
                "ok": False
            }

    # Trunca para não exceder contexto do LLM
    content_truncated = content[:3000]

    prompt = f"""Você é um engenheiro sênior de software avaliando código gerado por IA.

Avalie os seguintes critérios (seja objetivo e rígido):
- Funcionalidade: o código parece executar corretamente?
- Organização: estrutura clara, sem código redundante?
- Boas práticas: nomes significativos, sem magic numbers?
- Completude: está completo (não é pseudocódigo ou placeholder)?

Código a avaliar:
```
{content_truncated}
```

Responda SOMENTE com JSON válido:
{{
  "score": 0.85,
  "issues": ["lista de problemas encontrados"],
  "improvements": ["sugestões de melhoria"],
  "complete": true
}}

Regras do score:
- 0.0-0.3: quebrado ou pseudocódigo
- 0.3-0.6: parcialmente funcional
- 0.6-0.8: funcional mas com problemas
- 0.8-1.0: bem implementado"""

    res = ask("quality_evaluator", prompt, timeout=60)

    try:
        data = safe_json_load(res)
        score = float(data.get("score", 0.5))
        score = max(0.0, min(1.0, score))  # clamp 0-1

        return {
            "score": score,
            "issues": data.get("issues", []),
            "improvements": data.get("improvements", []),
            "ok": score >= 0.7
        }

    except Exception as e:
        # Se LLM falhar, avalia heurísticamente
        return _heuristic_quality(content)


def _heuristic_quality(code: str) -> dict:
    """
    Avalia qualidade sem LLM usando heurísticas simples.
    Usado como fallback quando o LLM não responde.
    """
    score = 0.5
    issues = []

    if len(code) < 50:
        score = 0.1
        issues.append("Código muito curto")
        return {"score": score, "issues": issues, "improvements": [], "ok": False}

    # Indicadores positivos
    if "def " in code or "class " in code:
        score += 0.1
    if "import " in code:
        score += 0.05
    if "#" in code:  # tem comentários
        score += 0.05
    if "if __name__" in code:
        score += 0.1

    # Indicadores negativos
    if "TODO" in code.upper() or "FIXME" in code.upper():
        score -= 0.1
        issues.append("Contém TODOs não implementados")
    if "pass" in code and code.count("pass") > 3:
        score -= 0.2
        issues.append("Muitos 'pass' — código não implementado")
    if "..." in code and code.count("...") > 2:
        score -= 0.15
        issues.append("Código com placeholders '...'")

    score = max(0.0, min(1.0, score))

    return {
        "score": score,
        "issues": issues,
        "improvements": ["Avaliação heurística — LLM indisponível"],
        "ok": score >= 0.6
    }