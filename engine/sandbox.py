import subprocess
import os

def run_in_docker(project_path):

    try:
        result = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{project_path}:/app",
             "python:3.11",
             "python", "/app/main.py"],
            capture_output=True,
            text=True,
            timeout=120
        )

        return result.stdout

    except Exception as e:
        return str(e)