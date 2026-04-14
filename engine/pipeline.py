import threading

pipeline_lock = threading.Lock()

from core.orchestrator import route

from agents.agent_a_game import agent_a
from agents.agent_b_saas import agent_b
from agents.agent_c_dev import agent_c

from engine.executor import run_project
from engine.security import security_check
from engine.quality import quality_check
from engine.autofix import auto_fix

from tools.git_manager import git_sync


def run_pipeline(task, user_id=None):

    with pipeline_lock:  # 🔥 1 request por vez (NÍVEL PRODUÇÃO)

        decision = route(task)

        r = decision.get("route", "C")

        if r == "A":
            project = agent_a(task)
        elif r == "B":
            project = agent_b(task)
        else:
            project = agent_c(task)

        output = run_project(project)

        # 🔥 proteção absoluta
        if not output:
            return {
                "status": "error",
                "reason": "empty_output"
            }

        sec = security_check(output)

        if not sec.get("approved", True):
            project = auto_fix(project, sec)

        qa = quality_check(output)

        if float(qa.get("score", 1)) < 0.7:
            project = auto_fix(project, qa)

        git_sync(task)

        return {
            "status": "success",
            "route": r,
            "project": project
        }