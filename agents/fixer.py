"""
Fixer Agent — Corrige projetos com erros usando LLM.
"""
import os
from core.llm import ask
from core.json_utils import extract_files_from_llm
from core.workspace import write_files_to_project


def fix(project_path: str, error: str, error_type: str = "unknown") -> str:
    """
    Analisa os erros do projeto e aplica correções via LLM.

    Args:
        project_path: Caminho do diretório do projeto
        error: Descrição do erro ocorrido
        error_type: Categoria do erro (syntax, dependency, etc)
    """
    if not os.path.isdir(project_path):
        print(f"⚠️ fix(): caminho inválido: {project_path}")
        return project_path

    # Lê todos os arquivos do projeto para contexto
    project_files = {}
    for root, _, files in os.walk(project_path):
        for fname in files:
            ext = os.path.splitext(fname)[1]
            if ext in (".py", ".html", ".js", ".css", ".json", ".txt", ".md", ".yaml"):
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

    # Identifica o entry point principal
    existing_files = list(project_files.keys())
    
    files_str = "\n\n".join(
        f"=== {fname} ===\n{content[:3000]}"
        for fname, content in project_files.items()
    )

    prompt = f"""Você é um ENGENHEIRO DE SOFTWARE EXTRAORDINÁRIO (Elite Diamond Debugger).
Sua missão é salvar um projeto que falhou na execução.

CATEGORIA DO ERRO: {error_type.upper()}
DETALHES DO ERRO:
{error[:1500]}

ESTRUTURA ATUAL DO PROJETO:
{existing_files}

CONTEÚDO DOS ARQUIVOS:
{files_str[:8000]}

MISSÃO:
1. ANALISE: Identifique a causa raiz. Se for DEPENDENCY, corrija o `requirements.txt`. Se for SYNTAX ou IMPORT, corrija o código.
2. PRECISÃO CIRÚRGICA: Corrija APENAS o necessário. NUNCA crie novos arquivos com nomes parecidos aos existentes (ex: se existe `main.py`, nunca crie `mainn.py`).
3. ENTRYPOINT: Garanta que o arquivo principal (geralmente na raiz ou `app/`) esteja correto e chame os outros módulos adequadamente.
4. ROBUSTEZ: Use tratamento de erros e logging se necessário.

FORMATO DE RETORNO (APENAS ARQUIVOS MODIFICADOS):
```linguagem # caminho/do/arquivo.ext
# Solução: <breve explicação da correção>
<código completo corrigido>
```

REGRAS DIAMANTE:
- NUNCA use placeholders.
- NÃO CRIE ARQUIVOS DUPLICADOS OU COM ERRO DE GRAFIA.
- Mantenha a compatibilidade com Windows (caminhos com / ou \\).
"""

    response = ask("senior_debugger", prompt, timeout=180)

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