import os

def score_project(path):
    score = 0

    for root, _, files in os.walk(path):

        if "package.json" in files:
            score += 3

        if "requirements.txt" in files:
            score += 3

        if "index.html" in files:
            score += 2

        if any(f.endswith(".js") for f in files):
            score += 2

        if any(f.endswith(".py") for f in files):
            score += 2

    return score


def choose_best(projects, user):
    print("🧠 Avaliando projetos...")

    best = None
    best_score = -1

    for p in projects:
        s = score_project(p)
        print(f"📊 {p} → score {s}")

        if s > best_score:
            best_score = s
            best = p

    return best