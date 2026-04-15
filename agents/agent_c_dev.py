"""
Agent C — Dev / Automation Specialist
Especializado em scripts, automação, processamento de dados e ferramentas CLI.
"""
from core.llm import ask
from core.json_utils import extract_files_from_llm
from core.workspace import create_project_dir, write_files_to_project, save_project_manifest


def agent_c(task: str, model: str = None, mode: str = "fast") -> str:
    """
    Gera scripts e ferramentas de automação funcionais.

    Returns:
        Caminho da pasta do projeto gerado
    """
    print(f"⚙️ [DEV AGENT] Criando automação: {task[:60]}...")

    prompt = f"""Você é o ENGENHEIRO DE AUTOMAÇÃO DIAMOND (Elite).
FILOSOFIA OBRIGATÓRIA: NUNCA REMOVA SEM NECESSIDADE VITAL, SOMENTE MELHORE E CORRIJA, MELHORIA CONTINUA E EXCELENCIA!

Seu objetivo é criar ferramentas de automação INFALÍVEIS e de NÍVEL INDUSTRIAL.

TAREFA: {task}

REQUISITOS TÉCNICOS DIAMANTE:
1. PERFORMANCE: Use `asyncio` para I/O intensivo.
2. ROBUSTEZ: Tratamento de exceções granular e lógica de retry.
3. SUÍTE DE TESTES (OBRIGATÓRIO): Crie um arquivo `test_main.py` com `pytest` que valide as funções principais.
4. DADOS REAIS: Para tarefas financeiras/ações, use bibliotecas como `yfinance` ou `pandas`.
5. DOCUMENTAÇÃO: Docstrings PEP 257 e Type Hinting 100%.
6. NO-PLACEHOLDERS: 100% da lógica implementada.

FORMATO DE SAÍDA:
```linguagem # nome_do_arquivo.ext
# Documentação Industrial
# Código Diamond Robusto
```

Arquivos esperados: `main.py`, `test_main.py`, `requirements.txt`, `manual.md`."""

    # Tenta usar CrewAI para orquestração de 2 agentes (Lead + Developer)
    try:
        from core.crew_factory import run_diamond_crew
        print("🤝 [DIAMOND CREW] Iniciando colaboração de elite (2 Agentes)...")
        response = run_diamond_crew(f"Create an automation script following these rules: {prompt}", model_name=model)
    except Exception as e:
        print(f"⚠️ CrewAI não disponível ou falhou ({e}), usando agente único...")
        response = ask("dev_engineer", prompt, model=model, timeout=180)

    if not response or len(response) < 50:
        return _fallback_script(task)

    files = extract_files_from_llm(response)

    if not files or not any(files.values()):
        # Tenta usar resposta inteira como script Python
        import re
        code_match = re.search(r"```(?:python)?\n(.*?)```", response, re.DOTALL)
        if code_match:
            files = {"main.py": code_match.group(1).strip()}
        else:
            return _fallback_script(task)

    if "requirements.txt" not in files:
        files["requirements.txt"] = "# Nenhuma dependência externa necessária\n"

    if "manual.md" not in files:
        files["manual.md"] = f"# {task[:50]}\n\nScript gerado automaticamente.\n\n## Executar\n```bash\npython main.py\n```\n"

    project_path = create_project_dir(task)
    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "C", created)

    print(f"  ✅ Script salvo em: {project_path}")
    return project_path


def _fallback_script(task: str) -> str:
    """Script de sistema de arquivos como fallback."""
    script = f'''#!/usr/bin/env python3
"""
Script gerado para: {task}
"""
import os
import json
from pathlib import Path
from datetime import datetime

def main():
    print(f"🤖 Executando: {task[:60]}")
    print(f"📅 Data: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print(f"📁 Diretório: {{os.getcwd()}}")

    # Exemplo: lista arquivos do diretório atual
    files = list(Path(".").iterdir())
    print(f"\\n📂 Arquivos encontrados: {{len(files)}}")
    for f in sorted(files)[:20]:
        size = f.stat().st_size if f.is_file() else 0
        print(f"  {{\'📄\' if f.is_file() else \'📁\'}} {{f.name}} {{f\'({{size}} bytes)\' if f.is_file() else \'\'}}")

    print("\\n✅ Script executado com sucesso!")

if __name__ == "__main__":
    main()
'''
    project_path = create_project_dir(task)
    files = {
        "main.py": script,
        "requirements.txt": "# Sem dependências externas\n",
        "README.md": f"# Script\n\n{task}\n\n## Executar\n```bash\npython main.py\n```\n"
    }
    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "C", created)
    return project_path