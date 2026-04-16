"""
TODOS os agentes DEVEM obedecer isso.
"""

def agent_contract():
    return {
        "input": {
            "task": str,
            "context": dict
        },
        "output": {
            "status": "success|fail",
            "data": dict,
            "logs": list,
            "errors": list
        }
    }