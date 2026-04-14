import os
import re
import subprocess
from github_fetcher import github_fetch

KNOWLEDGE_DIR = "knowledge"
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# =========================
# FILTRO DE QUALIDADE
# =========================
def is_good_repo(path):
    name = path.lower()

    bad = ["awesome", "tutorial", "course", "list"]

    if any(b in name for b in bad):
        return False

    # precisa ter código real
    for root, dirs, files in os.walk(path):
        if any(f.endswith((".html", ".js", ".py")) for f in files):
            return True

    return False


# =========================
# SALVAR NA MEMÓRIA
# =========================
def save_to_knowledge(path):
    name = os.path.basename(path)
    dest = os.path.join(KNOWLEDGE_DIR, name)

    if not os.path.exists(dest):
        os.rename(path, dest)

    return dest


# =========================
# ANALISAR PROJETO
# =========================
def analyze_project(path):
    score = 0

    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".html"):
                score += 2
            if f.endswith(".js"):
                score += 4
            if f.endswith(".py"):
                score += 3
            if f == "index.html":
                score += 10

    return score


# =========================
# ESCOLHER MELHOR
# =========================
def pick_best(folders):
    best = None
    best_score = 0

    for f in folders:
        score = analyze_project(f)
        print(f"📊 {f} → {score}")

        if score > best_score:
            best_score = score
            best = f

    return best


# =========================
# EXECUTAR COM LOG
# =========================
def run_with_log(path):
    for root, dirs, files in os.walk(path):
        if "index.html" in files:
            file = os.path.join(root, "index.html")
            os.startfile(file)
            return True, ""

        for f in files:
            if f.endswith(".py"):
                file = os.path.join(root, f)
                result = subprocess.run(
                    ["python", file],
                    capture_output=True,
                    text=True
                )
                return False, result.stderr

    return False, "Nada executável"


# =========================
# AUTO FIX SIMPLES
# =========================
def auto_fix(path, error):
    print("🛠️ Tentando corrigir erro...")

    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)

                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    code = file.read()

                # exemplo simples de correção
                if "No module named" in error:
                    module = error.split("No module named")[-1].strip().replace("'", "")
                    print(f"📦 Instalando {module}")
                    os.system(f"pip install {module}")

                # salva de novo (pode expandir com mais regras)
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(code)


# =========================
# BUSCA INTELIGENTE
# =========================
def search_projects(user):
    queries = [
        f"{user} full project",
        f"{user} complete app",
        f"{user} github project",
        f"{user} source code",
        f"{user} working project",
    ]

    folders = []

    for q in queries:
        print(f"🔎 {q}")

        try:
            results = github_fetch(q)
        except:
            continue

        if results:
            for r in results:
                if is_good_repo(r):
                    folders.append(r)

        if len(folders) >= 10:
            break

    return folders


# =========================
# MAIN
# =========================
user = input("💬 O que você quer criar? ")

folders = search_projects(user)

if not folders:
    print("❌ Nada encontrado")
    exit()

# 🔥 salvar tudo como conhecimento
folders = [save_to_knowledge(f) for f in folders]

best = pick_best(folders)

print("🏆 Melhor:", best)

success, error = run_with_log(best)

# 🔥 AUTO FIX LOOP
tentativas = 0

while not success and tentativas < 3:
    print("⚠️ Erro detectado:")
    print(error)

    auto_fix(best, error)

    success, error = run_with_log(best)

    tentativas += 1

if success:
    print("🎉 Funcionou!")
else:
    print("❌ Não conseguiu corrigir")