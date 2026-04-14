from core.llm import ask
import os

def fix(path, error):
    code = ""

    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as file:
                    code += file.read()

    prompt = f"Corrija:\n{error}\n{code}"

    fixed = ask("fix_agent", prompt)

    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f), "w", encoding="utf-8") as file:
                    file.write(fixed)
                return