from crewai import Agent, Task, Crew
import subprocess
import time
import os
import re
from github_fetcher import github_fetch

# =========================
# CONFIG
# =========================
DEV_LLM = "ollama/gemma4:e4b"
FIX_LLM = "ollama/gemma4:e4b"
MAX_ATTEMPTS = 3

# =========================
# SLUGIFY
# =========================
def slugify(text):
    text = text.lower().strip()

    rep = {
        "ã":"a","á":"a","à":"a",
        "é":"e","ê":"e",
        "í":"i",
        "ó":"o","ô":"o",
        "ú":"u",
        "ç":"c"
    }

    for k,v in rep.items():
        text = text.replace(k,v)

    text = text.replace(" ", "-")
    text = re.sub(r'[^a-z0-9\-]', '', text)

    return text[:40]

# =========================
# DETECT STACK
# =========================
def detect_stack(user_request):
    text = user_request.lower()

    if "pwa" in text:
        return "pwa_game"

    if "jogo" in text or "game" in text:
        return "web_game"

    if "api" in text:
        return "python_api"

    return "python"

# =========================
# BUILD QUERY
# =========================
def build_search_query(user_request, stack):
    text = user_request.lower()

    if stack == "pwa_game":
        keywords = ["javascript", "html5", "game", "pwa"]

    elif stack == "web_game":
        keywords = ["javascript", "html5", "game", "canvas"]

    elif stack == "python_api":
        keywords = ["python", "flask", "api"]

    else:
        keywords = ["python"]

    if "avião" in text or "aviao" in text:
        keywords.append("airplane")

    if "tiro" in text:
        keywords.append("shooter")

    return " ".join(keywords)

# =========================
# GIT
# =========================
def git_sync():
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)

def create_branch(user_request):
    safe = slugify(user_request)
    branch = f"feat/{safe}-{int(time.time())}"

    subprocess.run(["git", "checkout", "-b", branch], check=False)
    print(f"🌿 Branch: {branch}")
    return branch

def git_commit_and_push(branch, user_request):
    try:
        safe = slugify(user_request)
        tag = f"v-{safe}-{int(time.time())}"

        subprocess.run(["git", "add", "."], check=False)
        subprocess.run(["git", "commit", "-m", user_request], check=False)
        subprocess.run(["git", "tag", tag], check=False)
        subprocess.run(["git", "push", "-u", "origin", branch], check=False)
        subprocess.run(["git", "push", "--tags"], check=False)

        print(f"🚀 Push: {branch} | {tag}")
    except Exception as e:
        print("⚠️ Git erro:", e)

# =========================
# AGENTES
# =========================
dev_agent = Agent(
    role="Developer",
    goal="Generate working code",
    backstory="Expert dev",
    llm=DEV_LLM,
    verbose=True
)

fix_agent = Agent(
    role="Debugger",
    goal="Fix errors",
    backstory="Expert debugger",
    llm=FIX_LLM,
    verbose=True
)

# =========================
# INPUT
# =========================
user_request = input("💬 O que você quer criar? ")

stack = detect_stack(user_request)
search_query = build_search_query(user_request, stack)

print(f"🧠 Stack: {stack}")
print(f"🔎 Query: {search_query}")

# =========================
# BUSCA
# =========================
folders = github_fetch(search_query)

print("DEBUG folders:", folders)

if not folders:
    print("⚠️ Nenhum repositório encontrado")
    folders = []

# =========================
# ESCOLHER PROJETO
# =========================
def find_best_project(folders):
    if not folders:
        return None

    for folder in folders:
        for root, dirs, files in os.walk(folder):
            if "index.html" in files:
                return root

    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.endswith(".py"):
                    return root

    return None

project_path = find_best_project(folders)

# =========================
# EXECUTAR
# =========================
def run_project(path):
    if not path:
        return "", "Sem projeto"

    index = os.path.join(path, "index.html")

    if os.path.exists(index):
        print("🌐 Abrindo navegador...")
        os.startfile(index)
        return "", ""

    for f in os.listdir(path):
        if f.endswith(".py"):
            return subprocess.run(
                ["python", os.path.join(path, f)],
                capture_output=True,
                text=True
            )

    return "", "Nada executável"

# =========================
# IA FALLBACK
# =========================
def generate_with_ai():
    task = Task(
        description=f"Create project: {user_request}",
        expected_output="Code",
        agent=dev_agent
    )

    crew = Crew(agents=[dev_agent], tasks=[task])
    return str(crew.kickoff())

# =========================
# GIT START
# =========================
git_sync()
branch = create_branch(user_request)

# =========================
# FALLBACK
# =========================
if not project_path:
    print("⚠️ Nenhum projeto válido. IA...")
    code = generate_with_ai()

    with open("generated.py", "w") as f:
        f.write(code)

    project_path = "."

git_commit_and_push(branch, user_request)

# =========================
# LOOP
# =========================
for attempt in range(MAX_ATTEMPTS):

    print(f"\n🔁 Tentativa {attempt+1}")

    stdout, stderr = run_project(project_path)

    if not stderr:
        print("🎉 Funcionou!")
        break

    print("❌ ERRO:", stderr)

    fix_task = Task(
        description=f"Fix error:\n{stderr}",
        expected_output="Fixed code",
        agent=fix_agent
    )

    fix_crew = Crew(agents=[fix_agent], tasks=[fix_task])
    fix_crew.kickoff()

    git_commit_and_push(branch, user_request)

else:
    print("⚠️ Não resolveu completamente")