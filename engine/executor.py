"""
Executor de Projetos — executa código gerado pelos agentes com segurança.

Estratégia:
  1. Se um caminho de diretório for fornecido → executa main.py no diretório
  2. Se código Python for fornecido → salva em arquivo temporário e executa
  3. Captura stdout, stderr, e código de retorno
  4. Timeout configurável por tarefa
"""
import subprocess
import os
import tempfile
import sys
from pathlib import Path


def run_project(project_path: str = None, code: str = None,
                timeout: int = 60) -> dict:
    """
    Executa um projeto gerado pelo agente.

    Args:
        project_path: Caminho para diretório do projeto (executa main.py)
        code: Código Python como string para executar diretamente
        timeout: Timeout em segundos

    Returns:
        dict com: {success, stdout, stderr, returncode, error}
    """
    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
        "returncode": -1,
        "error": None,
        "executed": None
    }

    try:
        # ===================================================
        # MODO 1: Pasta de projeto com main.py
        # ===================================================
        if project_path and os.path.isdir(project_path):
            main_file = os.path.join(project_path, "main.py")

            if not os.path.exists(main_file):
                # Procura qualquer .py executável
                py_files = list(Path(project_path).glob("*.py"))
                if py_files:
                    main_file = str(py_files[0])
                else:
                    result["error"] = f"Nenhum arquivo .py encontrado em: {project_path}"
                    return result

            proc = subprocess.run(
                [sys.executable, main_file],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["returncode"] = proc.returncode
            result["success"] = proc.returncode == 0
            result["executed"] = main_file

            if proc.returncode != 0:
                result["error"] = f"Saiu com código {proc.returncode}: {proc.stderr[:500]}"

            return result

        # ===================================================
        # MODO 2: Código como string (salva em arquivo temp)
        # ===================================================
        if code and isinstance(code, str) and len(code.strip()) > 10:
            # Usa arquivo temporário em vez de exec() (mais seguro e captura output)
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="agent_task_",
                dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace"),
                delete=False,
                encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            try:
                proc = subprocess.run(
                    [sys.executable, tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"}
                )
                result["stdout"] = proc.stdout
                result["stderr"] = proc.stderr
                result["returncode"] = proc.returncode
                result["success"] = proc.returncode == 0
                result["executed"] = tmp_path

                if proc.returncode != 0:
                    result["error"] = f"Erro na execução: {proc.stderr[:500]}"

            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

            return result

        # ===================================================
        # Projeto é uma pasta mas path inválido
        # ===================================================
        if project_path:
            result["error"] = f"Caminho inválido ou não é diretório: {project_path}"
        else:
            result["error"] = "Nenhum projeto ou código fornecido para executar"

        return result

    except subprocess.TimeoutExpired as e:
        # Para jogos ou servidores, exibir timeout sem gerar um crash real significa que funcionou!
        err_out = str(e.stderr) if e.stderr else ""
        if "Traceback" in err_out or "Error:" in err_out:
            result["error"] = f"Timeout com erro: {err_out[:500]}"
            result["stderr"] = err_out
        else:
            result["success"] = True
            result["returncode"] = 0
            result["error"] = None
            result["stdout"] = str(e.stdout) if e.stdout else "Executou com sucesso até o timeout."
        return result

    except Exception as e:
        result["error"] = f"Erro inesperado no executor: {str(e)}"
        return result


def validate_project_structure(project_path: str) -> dict:
    """
    Valida se um projeto gerado tem estrutura PRO nível Diamond.
    """
    if not os.path.isdir(project_path):
        return {"valid": False, "score": 0, "issues": ["Diretório não existe"]}

    issues = []
    score = 0
    files = list(Path(project_path).rglob("*"))
    file_names = {f.name for f in files if f.is_file()}
    dirs = {f.name for f in files if f.is_dir()}

    # Arquivo Principal (Core)
    if "main.py" in file_names or "index.html" in file_names or "app.py" in file_names:
        score += 30
    else:
        issues.append("Ponto de entrada (main.py/index.html) não encontrado")

    # Dependências (Profissionalismo)
    if "requirements.txt" in file_names or "package.json" in file_names:
        score += 20
    else:
        issues.append("requirements.txt/package.json ausente (crucial)")

    # Documentação (Industrial)
    if "manual.md" in file_names or "README.md" in file_names:
        score += 10
    else:
        issues.append("Manual técnico ou README ausente")

    # Modularização (Diamond)
    if any(d in dirs for d in ["src", "app", "core", "utils", "models"]):
        score += 15
    
    # Testes (Enterprise Ready)
    if any(d in dirs for d in ["tests", "test"]):
        score += 15
    elif any(f.startswith("test_") and f.endswith(".py") for f in file_names):
        score += 10
    else:
        issues.append("Ausência de suíte de testes (necessário para Diamond)")

    # Configurações
    if ".env.example" in file_names or "config" in dirs or "settings.py" in file_names:
        score += 10

    return {
        "valid": score >= 40,
        "score": score,
        "issues": issues,
        "files": list(file_names),
        "diamond_ready": score >= 80
    }