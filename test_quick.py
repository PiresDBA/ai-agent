import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.pipeline import run_pipeline

def test_agent(name, task):
    print(f"\n\n>>> ======= TESTING {name} =======")
    print(f"Task: {task}")
    res = run_pipeline(task)
    print(f"\n=> RESULT {name}: status={res['status']}")
    print(f"=> PATH: {res.get('project_path')}")
    print(f"=> SCORE: {res.get('score')}")
    if res['status'] == 'failed':
        print(f"=> ERROR: {res.get('error')}")
    return res

if __name__ == '__main__':
    # Test Agent A
    # test_agent("Agent A (Game)", "simple snake game with pygame")
    
    # Test Agent B
    # test_agent("Agent B (SaaS)", "simple notes api fastapi")
    
    # Test Agent C
    test_agent("Agent C (Dev)", "professional script to monitor battery and system cpu usage, logging to CSV with proper rotating logs and error handling")
