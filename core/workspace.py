"""
Workspace Manager — Gerencia a criação e organização de projetos na workspace.

Cada tarefa recebe uma pasta isolada em workspace/<timestamp>_<slug>/
O agente escreve os arquivos nessa pasta.
"""
import os
import re
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace")


def slugify(text: str) -> str:
    """Converte texto em slug válido para nome de pasta."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:40] or "project"


def create_project_dir(task: str) -> str:
    """Cria diretório isolado para o projeto da tarefa."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(task[:50])
    project_name = f"{timestamp}_{slug}"
    project_path = os.path.join(BASE_WORKSPACE, project_name)
    os.makedirs(project_path, exist_ok=True)
    return project_path


def write_files_to_project(project_path: str, files: dict[str, str]) -> list[str]:
    """
    Escreve um dicionário {filename: content} no diretório do projeto.
    Retorna lista de arquivos criados.
    """
    created = []

    for filename, content in files.items():
        if not filename or not content:
            continue

        # Segurança: não permite paths absolutos ou escape de diretório
        filename = filename.replace("..", "").lstrip("/\\")
        full_path = os.path.join(project_path, filename)

        # Cria subdiretórios se necessário
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)

        created.append(full_path)

    return created


def save_project_manifest(project_path: str, task: str, route: str, files: list[str]):
    """Salva metadados do projeto em project.json."""
    manifest = {
        "task": task,
        "route": route,
        "created_at": datetime.now().isoformat(),
        "files": [os.path.basename(f) for f in files],
        "project_path": project_path
    }
    manifest_path = os.path.join(project_path, "project.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def list_projects() -> list[dict]:
    """Lista todos os projetos na workspace com seus manifestos."""
    projects = []

    if not os.path.exists(BASE_WORKSPACE):
        return []

    for item in sorted(os.listdir(BASE_WORKSPACE), reverse=True):
        item_path = os.path.join(BASE_WORKSPACE, item)
        if not os.path.isdir(item_path):
            continue

        manifest_path = os.path.join(item_path, "project.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                projects.append(manifest)
            except Exception:
                projects.append({"project_path": item_path, "task": item})
        else:
            projects.append({"project_path": item_path, "task": item})

    return projects


def get_project(project_path: str) -> dict:
    """Retorna conteúdo de todos os arquivos de um projeto."""
    result = {"path": project_path, "files": {}}

    if not os.path.isdir(project_path):
        return result

    for root, _, files in os.walk(project_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, project_path)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    result["files"][rel] = f.read()
            except Exception:
                result["files"][rel] = "[binary ou ilegível]"

    return result


def cleanup_old_projects(max_projects: int = 50):
    """Remove projetos mais antigos quando passa do limite."""
    if not os.path.exists(BASE_WORKSPACE):
        return

    projects = sorted(
        [d for d in os.listdir(BASE_WORKSPACE) if os.path.isdir(os.path.join(BASE_WORKSPACE, d))]
    )

    while len(projects) > max_projects:
        oldest = projects.pop(0)
        shutil.rmtree(os.path.join(BASE_WORKSPACE, oldest), ignore_errors=True)
