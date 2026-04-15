"""
Fixer Agent — Corrige projetos com erros usando LLM.
"""
import os
from core.llm import ask
from core.json_utils import extract_files_from_llm
from core.workspace import write_files_to_project


def fix(project_path: str, error: str) -> str:
    """
    Analisa os erros do projeto e aplica correções via LLM.

    Args:
        project_path: Caminho do diretório do projeto
        error: Descrição do erro ocorrido

    Returns:
        Caminho do projeto (mesmo, com arquivos corrigidos)
    """
    if not os.path.isdir(project_path):
        print(f"⚠️ fix(): caminho inválido: {project_path}")
        return project_path

    # Lê todos os arquivos do projeto
    project_files = {}
    for root, _, files in os.walk(project_path):
        for fname in files:
            ext = os.path.splitext(fname)[1]
            if ext in (".py", ".html", ".js", ".css", ".json", ".txt", ".md"):
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, project_path)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        project_files[rel] = f.read()
                except Exception:
                    pass

    if not project_files:
        print("⚠️ fix(): nenhum arquivo encontrado para corrigir")
        return project_path

    files_str = "\n\n".join(
        f"=== {fname} ===\n{content[:2000]}"
        for fname, content in project_files.items()
    )

    prompt = f"""Você é um ENGENHEIRO DE SOFTWARE EXTRAORDINÁRIO, especialista em Debugging e Refatoração.
Sua missão é salvar um projeto que falhou na execução ou tem baixa qualidade.

ERRO REPORTADO:
{error[:1500]}

ARQUIVOS DO PROJETO:
{files_str[:6000]}

TAREFA:
1. Analise meticulosamente a causa raiz (Considere: caminhos de arquivo, dependências, erros de sintaxe e lógica).
2. Corrija o código para que ele seja 100% EXECUTÁVEL e ROBUSTO.
3. Se o erro for "missing dep", verifique se o requirements.txt está correto.
4. Aplique conceitos de "Chain of Thought": descreva brevemente o problema (dentro de um comentário no código) e a solução aplicada.

FORMATO DE RETORNO (OBRIGATÓRIO PARA TODOS OS ARQUIVOS MODIFICADOS):
```linguagem # nome_do_arquivo.ext
# Solução: <breve explicação>
<código completo corrigido>
```

REGRAS:
- NUNCA use placeholders.
- Mantenha a compatibilidade com o Windows.
- Retorne apenas os arquivos que precisaram de alteração."""

    response = ask("fixer_agent", prompt, timeout=180)

    if not response or len(response) < 30:
        print("⚠️ fix(): LLM não retornou correção")
        return project_path

    fixed_files = extract_files_from_llm(response)

    if fixed_files:
        created = write_files_to_project(project_path, fixed_files)
        print(f"✅ fix(): {len(created)} arquivo(s) corrigido(s): {list(fixed_files.keys())}")
    else:
        print("⚠️ fix(): não foi possível extrair arquivos da resposta LLM")

    return project_path