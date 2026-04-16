"""
Memória persistente do sistema de agentes.
Armazena histórico de tarefas, rotas e resultados.
"""
import json
import os
import hashlib
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(BASE_DIR, "data", "memory.json")


def _ensure_dir():
    os.makedirs(os.path.dirname(FILE), exist_ok=True)


def hash_task(task: str) -> str:
    return hashlib.md5(task.encode("utf-8")).hexdigest()


def _load() -> dict:
    _ensure_dir()
    if not os.path.exists(FILE):
        return {"success": [], "failed": [], "stats": {}}
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"success": [], "failed": [], "stats": {}}


def _save(data: dict):
    _ensure_dir()
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def remember_success(task: str, route: str, score: float, project_path: str):
    """Registra uma tarefa concluída com sucesso."""
    data = _load()
    data["success"].append({
        "task_id": hash_task(task),
        "task_preview": task[:100],
        "route": route,
        "score": score,
        "project_path": project_path,
        "timestamp": datetime.now().isoformat()
    })
    # Mantém apenas os últimos 500 registros
    data["success"] = data["success"][-500:]
    _save(data)


def remember_failure(task: str, route: str, error: str):
    """Registra uma tarefa que falhou."""
    data = _load()
    data.setdefault("failed", []).append({
        "task_id": hash_task(task),
        "task_preview": task[:100],
        "route": route,
        "error": error[:500],
        "timestamp": datetime.now().isoformat()
    })
    data["failed"] = data["failed"][-200:]
    _save(data)


def get_best_route_hint(task: str) -> Optional[str]:
    """Retorna a rota mais bem-sucedida para tarefas similares."""
    data = _load()
    task_id = hash_task(task)

    for item in reversed(data.get("success", [])):
        if item.get("task_id") == task_id:
            return item.get("route")

    return None


def get_stats() -> dict:
    """Retorna estatísticas do sistema."""
    data = _load()
    successes = data.get("success", [])
    failures = data.get("failed", [])

    total = len(successes) + len(failures)
    avg_score = (sum(s.get("score", 0) for s in successes) / len(successes)) if successes else 0

    return {
        "total_tasks": total,
        "successes": len(successes),
        "failures": len(failures),
        "success_rate": len(successes) / total if total > 0 else 0,
        "average_score": round(avg_score, 3),
        "last_task": successes[-1]["task_preview"] if successes else None
    }