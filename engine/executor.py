import subprocess
import os

def run_project(project_path=None, code=None):
    """
    Executa projeto localmente ou código gerado
    """

    try:
        # =========================
        # CASO 1: projeto em pasta
        # =========================
        if project_path:
            result = subprocess.run(
                ["python", "main.py"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout

        # =========================
        # CASO 2: código direto
        # =========================
        if code:
            exec_globals = {}
            exec(code, exec_globals)
            return "executado em memória"

        return "nenhum input fornecido"

    except Exception as e:
        return f"erro execução: {e}"