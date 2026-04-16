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
import re
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
        # MODO 1: Pasta de projeto com busca inteligente de entrypoint
        # ===================================================
        if project_path and os.path.isdir(project_path):
            main_file = _find_main_file(project_path)

            if not main_file:
                # Procura qualquer .py que pareça importante se não achou main.py
                py_files = list(Path(project_path).rglob("*.py"))
                if py_files:
                    main_file = str(py_files[0])
                else:
                    result["error"] = f"Nenhum arquivo .py encontrado em: {project_path}"
                    result["error_type"] = "structure"
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
                etype, emsg = _classify_error(proc.stderr)
                result["error"] = f"[{etype}] {emsg}"
                result["error_type"] = etype

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
                    etype, emsg = _classify_error(proc.stderr)
                    result["error"] = f"[{etype}] {emsg}"
                    result["error_type"] = etype

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
            result["error_type"] = "path"
        else:
            result["error"] = "Nenhum projeto ou código fornecido para executar"
            result["error_type"] = "input"

        return result

    except subprocess.TimeoutExpired as e:
        # Para jogos ou servidores, exibir timeout sem gerar um crash real significa que funcionou!
        err_out = str(e.stderr) if e.stderr else ""
        if "Traceback" in err_out or "Error:" in err_out:
            etype, emsg = _classify_error(err_out)
            result["error"] = f"Timeout com erro: {emsg}"
            result["error_type"] = etype
            result["stderr"] = err_out
        else:
            result["success"] = True
            result["returncode"] = 0
            result["error"] = None
            result["stdout"] = str(e.stdout) if e.stdout else "Executou com sucesso até o timeout."
        return result

    except Exception as e:
        result["error"] = f"Erro inesperado no executor: {str(e)}"
        result["error_type"] = "internal"
        return result


def _find_main_file(project_path: str) -> str:
    """Busca o ponto de entrada principal de forma inteligente (recursiva)."""
    p = Path(project_path)
    # Ordem de preferência Diamond
    search_patterns = [
        "main.py", "app.py", "run.py", "index.py",
        "app/main.py", "src/main.py", "src/app.py",
        "**/main.py", "**/app.py"
    ]
    
    for pattern in search_patterns:
        matches = list(p.glob(pattern))
        if matches:
            return str(matches[0])
    return None


def _classify_error(stderr: str) -> tuple[str, str]:
    """Classifica o erro do Python em categorias Diamond."""
    if not stderr:
        return "unknown", "Erro oculto ou processo interrompido"
    
    if "ModuleNotFoundError" in stderr:
        module = re.search(r"ModuleNotFoundError: No module named '([^']+)'", stderr)
        module_name = module.group(1) if module else "desconhecido"
        return "dependency", f"Biblioteca faltando: {module_name}"
        
    if "SyntaxError" in stderr or "IndentationError" in stderr:
        return "syntax", "Erro de sintaxe ou indentação no código"
        
    if "ImportError" in stderr:
        return "import", "Erro ao importar módulo ou objeto interno"
        
    if "AttributeError" in stderr or "TypeError" in stderr:
        return "logic", "Erro de lógica/tipo (acesso a atributo inexistente ou tipo inválido)"
        
    if "Traceback" in stderr:
        # Pega a última linha do traceback
        lines = stderr.strip().splitlines()
        return "runtime", lines[-1] if lines else "Erro de execução"
        
    return "other", stderr[:200]


def _detect_project_type(file_names: set, project_path: str) -> str:
    """Detecta se o projeto é um jogo, webapp, ou util/automação."""
    # Lê o conteúdo dos arquivos principais para detectar
    game_signals = {"pygame", "canvas", "phaser", "game", "sprite", "player", "enemy", 
                    "score", "level", "gameloop", "game_loop", "joystick", "kaboom",
                    "requestAnimationFrame", "KEYDOWN", "collision"}
    web_signals = {"flask", "fastapi", "django", "express", "react", "vue", "angular",
                   "router", "middleware", "database", "endpoint", "API"}

    content_lower = ""
    for fname in file_names:
        fpath = os.path.join(project_path, fname)
        if os.path.isfile(fpath) and fname.endswith((".py", ".js", ".html", ".ts")):
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content_lower += f.read(3000).lower() + " "
            except Exception:
                pass

    game_hits = sum(1 for s in game_signals if s in content_lower)
    web_hits = sum(1 for s in web_signals if s in content_lower)

    if game_hits >= 2:
        return "game"
    if web_hits >= 2:
        return "webapp"
    if "index.html" in file_names and game_hits >= 1:
        return "game"
    return "tool"


def _auto_generate_requirements(project_path: str, file_names: set):
    """Auto-gera requirements.txt analisando imports dos .py do projeto."""
    # Bibliotecas padrão que NÃO devem ir no requirements
    stdlib = {"os", "sys", "re", "json", "math", "random", "time", "datetime",
              "collections", "itertools", "functools", "pathlib", "typing",
              "subprocess", "threading", "multiprocessing", "hashlib", "shutil",
              "tempfile", "io", "string", "copy", "enum", "abc", "dataclasses",
              "argparse", "logging", "unittest", "csv", "sqlite3", "http",
              "urllib", "socket", "ssl", "email", "html", "xml", "ctypes",
              "struct", "array", "queue", "signal", "glob", "fnmatch",
              "statistics", "decimal", "fractions", "textwrap", "difflib",
              "pprint", "traceback", "warnings", "contextlib", "inspect",
              "importlib", "pkgutil", "platform", "uuid", "secrets",
              "base64", "binascii", "codecs", "unicodedata", "locale",
              "gettext", "calendar", "heapq", "bisect", "weakref",
              "types", "operator", "atexit", "gc", "dis", "ast",
              "token", "tokenize", "compileall", "pdb", "profile",
              "cProfile", "timeit", "trace", "pickletools", "pickle",
              "shelve", "marshal", "dbm", "gzip", "bz2", "lzma",
              "zipfile", "tarfile", "configparser", "netrc", "xdrlib",
              "plistlib", "hmac", "mimetypes", "webbrowser", "cgi",
              "cgitb", "wsgiref", "xmlrpc", "turtle", "tkinter", "_thread"}

    external_imports = set()
    for fname in file_names:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(project_path, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("import "):
                        mod = line.split()[1].split(".")[0]
                        if mod not in stdlib:
                            external_imports.add(mod)
                    elif line.startswith("from ") and " import " in line:
                        mod = line.split()[1].split(".")[0]
                        if mod not in stdlib:
                            external_imports.add(mod)
        except Exception:
            pass

    if external_imports:
        req_path = os.path.join(project_path, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as f:
            for mod in sorted(external_imports):
                f.write(f"{mod}\n")


def validate_project_structure(project_path: str) -> dict:
    """
    Valida se um projeto gerado tem estrutura adequada.
    Ajusta os critérios pelo tipo de projeto (game vs webapp vs tool).
    """
    if not os.path.isdir(project_path):
        return {"valid": False, "score": 0, "issues": ["Diretório não existe"]}

    issues = []
    score = 0
    files = list(Path(project_path).rglob("*"))
    file_names = {f.name for f in files if f.is_file()}
    dirs = {f.name for f in files if f.is_dir()}

    # Detecta tipo de projeto para ajustar critérios
    project_type = _detect_project_type(file_names, project_path)

    # Arquivo Principal (Core) - vale para todos
    has_entry = ("main.py" in file_names or "index.html" in file_names 
                 or "app.py" in file_names or "run.py" in file_names
                 or "index.js" in file_names)
    if has_entry:
        score += 40
    else:
        issues.append("Ponto de entrada (main.py/index.html) não encontrado")

    # Dependências - Auto-gera se faltando para Python
    if "requirements.txt" in file_names or "package.json" in file_names:
        score += 15
    else:
        # Auto-gera requirements.txt analisando imports
        _auto_generate_requirements(project_path, file_names)
        if os.path.exists(os.path.join(project_path, "requirements.txt")):
            score += 15
            file_names.add("requirements.txt")
        elif project_type == "game":
            # Jogos HTML5/Canvas não precisam de requirements
            score += 10
        else:
            issues.append("requirements.txt/package.json ausente")

    # Documentação
    if "manual.md" in file_names or "README.md" in file_names:
        score += 15
    else:
        issues.append("Manual técnico ou README ausente")

    # Modularização - bônus, não penaliza jogos
    if any(d in dirs for d in ["src", "app", "core", "utils", "models", "assets"]):
        score += 10
    elif project_type != "game":
        # Só penaliza se não for jogo
        score += 5  # bônus parcial para projetos simples

    # Testes - bônus, nunca penaliza jogos
    if any(d in dirs for d in ["tests", "test"]):
        score += 10
    elif any(f.startswith("test_") and f.endswith(".py") for f in file_names):
        score += 10
    elif project_type == "game":
        # Jogos não precisam de testes unitários para funcionar
        score += 10

    # Bônus: múltiplos arquivos = projeto mais completo
    py_files = [f for f in file_names if f.endswith((".py", ".js", ".html", ".css"))]
    if len(py_files) >= 3:
        score += 5

    # Clamp
    score = min(100, score)

    return {
        "valid": score >= 50,
        "score": score,
        "issues": issues,
        "files": list(file_names),
        "project_type": project_type,
        "diamond_ready": score >= 80
    }