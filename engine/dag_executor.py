from engine.executor import run_project
from engine.security import security_check
from engine.quality import quality_check
from engine.autofix import auto_fix


def execute_dag(project, max_rounds=3):

    for i in range(max_rounds):

        print(f"🔁 DAG ROUND {i+1}")

        output = run_project(project)

        sec = security_check(output) or {}
        if not sec.get("approved", False):
            project = auto_fix(project, sec)
            continue

        qa = quality_check(output) or {}
        if float(qa.get("score", 0)) < 0.7:
            project = auto_fix(project, qa)
            continue

        return project, output

    return project, output