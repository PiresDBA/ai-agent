import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.pipeline import run_pipeline

def test_a():
    print("\n\n>>> ======= TEST AGENT A (Game) =======")
    res = run_pipeline("pygame mario clone", mode="planning")
    print(f"\n=> RESULT A: status={res['status']}")
    print(f"=> PATH: {res['project_path']}")
    return res['status'] == 'success'

def test_b():
    print("\n\n>>> ======= TEST AGENT B (SaaS) =======")
    res = run_pipeline("kanban board react app", mode="planning")
    print(f"\n=> RESULT B: status={res['status']}")
    print(f"=> PATH: {res['project_path']}")
    return res['status'] == 'success'

def test_c():
    print("\n\n>>> ======= TEST AGENT C (Dev) =======")
    res = run_pipeline("crewai orchestrator python", mode="planning")
    print(f"\n=> RESULT C: status={res['status']}")
    print(f"=> PATH: {res['project_path']}")
    return res['status'] == 'success'

if __name__ == '__main__':
    test_a()
    test_b()
    test_c()
    print("\n[ALL TESTS FINISHED]")
