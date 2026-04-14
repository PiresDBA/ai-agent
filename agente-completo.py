from core.router import route

from agents.agent_a_game import agent_a
from agents.agent_b_saas import agent_b
from agents.agent_c_dev import agent_c

from agents.security_agent import security_agent
from agents.quality_agent import quality_agent

from tools.git_manager import git_sync
from agents.fixer import fix


def execute(user):

    decision = route(user)
    r = decision["route"]

    # =====================
    # AGENT A - GAME
    # =====================
    if r == "A":

        code = agent_a(user)

    # =====================
    # AGENT B - SAAS
    # =====================
    elif r == "B":

        code = agent_b(user)

    # =====================
    # AGENT C - DEV
    # =====================
    else:

        code = agent_c(user)

    # =====================
    # SECURITY LAYER
    # =====================
    sec = security_agent(code)

    if "approved" in sec and "false" in sec:
        code = fix(code, sec)

    # =====================
    # QUALITY LAYER
    # =====================
    qa = quality_agent(code)

    if "score" in qa and float(qa["score"]) < 0.7:
        code = fix(code, qa)

    # =====================
    # FINAL STEP
    # =====================
    git_sync(user)

    return {
        "route": r,
        "result": "completed",
        "code": code
    }