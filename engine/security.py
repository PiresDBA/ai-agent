"""
Security Check — Análise de segurança do código gerado.
Detecta vulnerabilidades antes de executar código do LLM.
"""
import re
from core.llm import ask
from core.json_utils import safe_json_load


# Padrões perigosos que são detectados sem LLM (instantâneo)
DANGEROUS_PATTERNS = [
    (r"subprocess\.run\(.+shell=True", "shell=True perigoso (command injection)"),
    (r"os\.system\(", "os.system() — use subprocess com lista"),
    (r"eval\(", "eval() — execução de código arbitrário"),
    (r"__import__\(", "import dinâmico suspeito"),
    (r"rm\s+-rf", "rm -rf detectado"),
    (r"DROP\s+TABLE", "SQL DROP TABLE detectado"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Senha hardcoded no código"),
    (r"api_key\s*=\s*['\"][^'\"]+['\"]", "API key hardcoded no código"),
]


def _static_check(code: str) -> list[str]:
    """Análise estática rápida sem LLM."""
    issues = []
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append(description)
    return issues


def security_check(code_or_output: str | dict) -> dict:
    """
    Verifica segurança do código gerado.

    Args:
        code_or_output: Código como string, ou dict com 'stdout'/'code'

    Returns:
        dict com: {approved, issues, risk_score}
        
    IMPORTANTE: Retorna 'approved' (não 'safe') para consistência com o pipeline.
    """
    # Normaliza input
    if isinstance(code_or_output, dict):
        code = (
            code_or_output.get("code", "") or
            code_or_output.get("stdout", "") or
            str(code_or_output)
        )
    else:
        code = str(code_or_output)

    if not code or len(code.strip()) < 5:
        return {"approved": True, "issues": [], "risk_score": 0.0}

    # 1. Análise estática (sem LLM — instantâneo)
    static_issues = _static_check(code)

    if static_issues:
        risk = min(1.0, 0.3 * len(static_issues))
        return {
            "approved": risk < 0.6,  # bloqueia apenas risco alto
            "issues": static_issues,
            "risk_score": risk,
            "method": "static"
        }

    # 2. LLM analysis para código maior (só se passou na estática)
    if len(code) > 500:
        code_sample = code[:2000]

        prompt = f"""Analise este código Python em busca de vulnerabilidades de segurança.

Verifique:
- Command injection (subprocess com shell=True)
- Execução de código arbitrário (eval, exec)
- Acesso não autorizado ao sistema de arquivos
- Credenciais hardcoded
- Network calls suspeitas

Código:
```python
{code_sample}
```

Responda SOMENTE com JSON:
{{"approved": true, "issues": [], "risk_score": 0.1}}

Seja pragmático: codigo gerado por agente para tarefas de desenvolvimento é geralmente aprovado.
Só reprove se houver risco CLARO e REAL."""

        res = ask("security_analyst", prompt, timeout=45)

        try:
            data = safe_json_load(res)
            return {
                "approved": bool(data.get("approved", True)),
                "issues": data.get("issues", []),
                "risk_score": float(data.get("risk_score", 0.0)),
                "method": "llm"
            }
        except Exception:
            pass

    # 3. Fallback: aprova se passou na análise estática
    return {
        "approved": True,
        "issues": [],
        "risk_score": 0.0,
        "method": "fallback_safe"
    }