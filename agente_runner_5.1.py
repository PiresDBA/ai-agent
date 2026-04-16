import os
from github_fetcher import github_fetch

# =========================
# CONFIG
# =========================
MIN_FILES = 5

# =========================
# FILTRO FORTE
# =========================
def is_real_project(path):
    file_count = 0
    has_entry = False

    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith((".html", ".js", ".py")):
                file_count += 1

            if f in ["index.html", "app.py", "main.py"]:
                has_entry = True

    if file_count < MIN_FILES:
        return False

    if not has_entry:
        return False

    return True

# =========================
# SCORE (INTELIGÊNCIA)
# =========================
def score_project(path):
    score = 0

    for root, dirs, files in os.walk(path):
        for f in files:

            if f.endswith(".html"):
                score += 2

            if f.endswith(".js"):
                score += 3

            if f.endswith(".py"):
                score += 2

            if "game" in f.lower():
                score += 5

    return score

# =========================
# ESCOLHER MELHOR
# =========================
def pick_best_project(folders):
    valid = []

    for folder in folders:
        if is_real_project(folder):
            valid.append(folder)

    print(f"✅ Projetos válidos: {len(valid)}")

    if not valid:
        return None

    ranked = sorted(valid, key=lambda x: score_project(x), reverse=True)

    return ranked[0]

# =========================
# EXECUTAR
# =========================
def run_project(path):
    for root, dirs, files in os.walk(path):
        if "index.html" in files:
            full = os.path.join(root, "index.html")
            os.startfile(full)
            print("🚀 Rodando HTML")
            return True

        for f in files:
            if f.endswith(".py"):
                os.system(f"python {os.path.join(root, f)}")
                print("🚀 Rodando Python")
                return True

    return False

# =========================
# MAIN
# =========================
user = input("💬 O que você quer criar? ")

query = user.replace("jogo", "game")

# 🔥 BUSCA GRANDE
folders = []
folders.extend(github_fetch(query))
folders.extend(github_fetch(query + " html5"))
folders.extend(github_fetch(query + " javascript"))

print("📦 Total baixado:", len(folders))

# =========================
# ESCOLHA
# =========================
best = pick_best_project(folders)

if not best:
    print("❌ Nenhum projeto >=90% encontrado → ABORTANDO")
    exit()

print("🏆 Melhor projeto:", best)

# =========================
# EXECUÇÃO
# =========================
run_project(best)