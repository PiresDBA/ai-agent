import os
import subprocess

def run(path):
    for root, _, files in os.walk(path):

        if "index.html" in files:
            os.startfile(os.path.join(root, "index.html"))
            return True, ""

        for f in files:
            if f.endswith(".py"):
                result = subprocess.run(
                    ["python", os.path.join(root, f)],
                    capture_output=True,
                    text=True
                )
                return False, result.stderr

    return False, "Nada executável"