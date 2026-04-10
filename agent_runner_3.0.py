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
FIX_LLM = "ollama/qwen3.5:4b"
MAX_ATTEMPTS = 3

# =========================
# SLUGIFY
# =========================
def slugify(text):
    text = text.lower().strip()

    replacements = {
        "ã":"a","á":"a","à":"a",
        "é":"e","ê":"e",
        "í":"i",
        "ó":"o","ô":"o",
        "ú":"u",
        "ç":"c"
    }

    for k,v in replacements.items():
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
# BUILD SEARCH QUERY
# =========================
def build_search_query(user_request, stack):
    text = user_request.lower()

    if stack == "pwa_game":
        keywords = ["javascript", "html5", "game", "pwa", "service-worker"]

    elif stack == "web_game":
        keywords = ["javascript", "html5", "game", "canvas"]

    elif stack == "python_api":
        keywords = ["python", "flask", "api"]

    else:
        keywords = ["python"]

    if "avião" in text or "aviao" in text:
        keywords.append("airplane")

    if "tiro" in text or "shooter" in text:
        keywords.append("shooter")

    if "corrida" in text:
        keywords.append("racing")

    return " ".join(keywords)

# =========================
# GIT
# =========================

def git_sync():
    try:
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=False)
        print("🔄 Repo sincronizado")
    except:
        print("⚠️ Falha ao sincronizar")
        
def create_branch(user_request):
    safe = slugify(user_request)
    branch = f"{safe}-{int(time.time())}"

    subprocess.run(["git", "checkout", "-b", branch], check=False)
    print(f"🌿 Branch: {branch}")
    return branch

def git_commit_and_push(branch, user_request):
    try:
        safe = slugify(user_request)
        tag = f"{safe}-{int(time.time())}"

        subprocess.run(["git", "add", "."], check=False)
        subprocess.run(["git", "commit", "-m", f"{user_request}"], check=False)
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
    role="Senior Developer",
    goal="Generate working code",
    backstory="Expert developer",
    llm=DEV_LLM,
    verbose=True
)

fix_agent = Agent(
    role="Debugger",
    goal="Fix errors",
    backstory="Expert in debugging",
    llm=FIX_LLM,
    verbose=True
)

# =========================
# INPUT
# =========================
user_request = input("💬 O que você quer criar? ")

stack = detect_stack(user_request)
search_query = build_search_query(user_request, stack)

print(f"🧠 Stack detectada: {stack}")
print(f"🔎 Busca: {search_query}")

# =========================
# BUSCA GITHUB
# =========================
github_fetch(search_query)

base_folder = os.path.join("github_projects", search_query.replace(" ", "_"))

# =========================
# ENCONTRAR PROJETO
# =========================
def find_project_folder(base):
    for root, dirs, files in os.walk(base):
        if "index.html" in files:
            return root
    return base

project_path = find_project_folder(base_folder)

# =========================
# EXECUÇÃO
# =========================
def run_project(path):
    index = os.path.join(path, "index.html")

    if os.path.exists(index):
        print("🌐 Abrindo no navegador...")
        os.startfile(index)
        return "", ""

    for f in os.listdir(path):
        if f.endswith(".py"):
            return subprocess.run(
                ["python", os.path.join(path, f)],
                capture_output=True,
                text=True
            )

    return "", "Nenhum executável"

# =========================
# FALLBACK IA
# =========================
def generate_with_ai():
    task = Task(
        description=f"""
Create a project based on:

{user_request}

Rules:
- Use best language
- Prefer PWA if game
- Output only code
""",
        agent=dev_agent
    )

    crew = Crew(agents=[dev_agent], tasks=[task])
    result = crew.kickoff()

    return str(result)

# =========================
# GIT START
# =========================
git_sync()
branch = create_branch(user_request)

# =========================
# SE NÃO TEM PROJETO
# =========================
if not os.listdir(base_folder):
    print("⚠️ Nada no GitHub. Gerando com IA...")
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

    # FIX
    fix_task = Task(
        description=f"Fix this error:\n{stderr}",
        agent=fix_agent
    )

    Crew(agents=[fix_agent], tasks=[fix_task]).kickoff()

    git_commit_and_push(branch, user_request)

else:
    print("⚠️ Não resolveu completamente")