"""
Agent B — SaaS / Web App Developer
Especializado em criar aplicações web, dashboards, APIs e sistemas.
"""
from core.llm import ask
from core.json_utils import extract_files_from_llm
from core.workspace import create_project_dir, write_files_to_project, save_project_manifest


import re
def agent_b(task: str, model: str = None, mode: str = "fast") -> str:
    """
    Gera uma aplicação web/SaaS completa e funcional.

    Returns:
        Caminho da pasta do projeto gerado
    """
    print(f"🌐 [SAAS AGENT] Criando aplicação: {task[:60]}...")

    # 1. DIAMOND INTELLIGENCE: Identifica referência de mercado
    ref_url = None
    ref_prompt = f"Para a tarefa '{task}', qual seria a URL real de uma referência mundial (ex: olx.com.br, trello.com, airbnb.com)? Responda apenas a URL ou 'NONE'."
    try:
        ref_suggestion = ask("DiamondIntelligence", ref_prompt, model=model, timeout=30).strip()
        if "http" in ref_suggestion:
            ref_url = ref_suggestion.split()[0]
    except: pass

    # 2. DIAMOND CLONER: Captura UI de referência se houver
    cloned_path = None
    if ref_url:
        print(f"💎 [DIAMOND CLONER] Usando referência mundial: {ref_url}")
        try:
            from tools.diamond_cloner import clone_site_diamond
            cloned_path = clone_site_diamond(ref_url, task)
        except Exception as e:
            print(f"⚠️ Falha no cloner: {e}")

    # 3. KNOWLEDGE & FETCH: Lógica e estrutura
    kb_context = ""
    try:
        from tools.github_fetcher import search_local_knowledge, github_fetch
        # 3.1. Busca no Conhecimento Local (KB) primeiro
        kb_context = search_local_knowledge(task)
        
        # 3.2. Se KB não for suficiente, busca no GitHub
        base_repo = None
        clean_task = re.sub(r'[^\w\s]', '', task)
        task_keywords = " ".join(clean_task.split()[:8])
        
        print(f"🔍 [DIAMOND SEARCH] Buscando lógica para: {task_keywords}")
        repos = github_fetch(task_keywords + " backend fastapi")
        base_repo = repos[0] if repos else None
        
        if not base_repo:
            repos = github_fetch(task_keywords + " webapp boilerplate")
            base_repo = repos[0] if repos else None
    except Exception as e:
        print("⚠️ Erro ao buscar conhecimento:", e)

    prompt = f"""IDENTIDADE:
Você é o App Agent, um agente especialista em desenvolvimento de aplicativos. Sua função é criar interfaces, telas, componentes visuais, fluxos de usuário e features de aplicativos mobile e web. Você pensa como um desenvolvedor full-stack focado em produto (Tech Lead).

{kb_context if kb_context else ""}

REGRAS DO QUE VOCÊ PODE FAZER:
- Criar interfaces de usuário (UI) e experiências (UX)
- Desenvolver telas, componentes e layouts
- Implementar navegação e fluxos entre telas
- Criar formulários, listas, modais, dashboards
- Estruturar a arquitetura do aplicativo (pastas, rotas, estados)
- Integrar APIs REST e GraphQL
- Implementar autenticação (login, cadastro, sessão)
- Criar aplicativos em: React, React Native, Next.js, Flutter, Vue
- Gerenciar estado com: Redux, Zustand, Context API, Provider

REGRAS DO QUE VOCÊ NÃO PODE FAZER:
- NÃO criar lógica de jogos (física, mecânicas, NPCs)
- NÃO criar automações de processos externos (scripts, bots, pipelines)
- NÃO criar infraestrutura de servidor (Docker, CI/CD, deploy)
- NÃO responder perguntas de chat genéricas fora do contexto do app
- NÃO executar tarefas que pertençam a outros agentes

PROTOCOLO DE EXECUÇÃO OBRIGATÓRIO:
1. Antes de qualquer código, defina: qual tela/feature, qual framework, qual o fluxo esperado
2. Crie primeiro a estrutura (esqueleto), depois o conteúdo, depois o estilo
3. Documente cada componente criado com: nome, função, props esperadas
4. Ao finalizar, verifique: (a) o fluxo faz sentido para o usuário? (b) o código está limpo e reutilizável? (c) existem casos de erro tratados?

PROTOCOLO DE FALHA:
- Se receber uma tarefa de outro agente: recuse gentilmente e redirecione
- Se não souber qual tecnologia usar: pergunte antes de agir
- Se encontrar um erro: descreva o erro, a causa provável e a solução proposta
- NUNCA crie código que você não consegue explicar linha por linha

SAÍDA PADRÃO:
Sempre entregue: Estrutura de arquivos → Código comentado → Como rodar → O que ainda falta

TAREFA ATUAL: {task}"""

    # 4. DIAMOND TRIAGE: Avalia se a tarefa é simples (Relatório/Informação) ou complexa (SaaS)
    triage_prompt = f"Analyze if this task is a 'simple_information_report' or a 'complex_saas_app': {task}\nRespond ONLY 'simple' or 'complex'."
    is_simple = False
    try:
        triage_res = ask("DiamondTriage", triage_prompt, model="llama3.2:3b", timeout=15).lower()
        if "simple" in triage_res:
            is_simple = True
            print("💡 [FAST TRACK] Tarefa SaaS identificada como simples. Respondendo sem orquestração pesada...")
    except: pass

    if is_simple:
        response = ask("saas_developer", prompt, model=model, timeout=120)
    else:
        # Tenta usar CrewAI para orquestração de 2 agentes (Lead + Developer)
        try:
            from core.crew_factory import run_diamond_crew
            print("🤝 [DIAMOND CREW] Iniciando colaboração de elite (2 Agentes)...")
            response = run_diamond_crew(f"Create a SaaS following these rules: {prompt}", model_name=model)
        except Exception as e:
            print(f"⚠️ CrewAI não disponível ou falhou ({e}), usando agente único...")
            response = ask("saas_developer", prompt, model=model, timeout=180)
    

    if not response or len(response) < 100:
        return _fallback_todo_app(task)

    files = extract_files_from_llm(response)

    if not files or not any(files.values()):
        return _fallback_todo_app(task)

    if "requirements.txt" not in files:
        files["requirements.txt"] = "fastapi\nuvicorn\n"

    if "manual.md" not in files:
        files["manual.md"] = _generate_readme(task, files)

    # 4. MERGE DIAMOND: Une Clone UI + Github Logic + LLM Glue
    project_path = create_project_dir(task)
    import shutil

    # Prioridade 1: Lógica do GitHub
    if base_repo and os.path.exists(base_repo):
        try:
            items = os.listdir(base_repo)
            src = os.path.join(base_repo, items[0]) if len(items) == 1 and os.path.isdir(os.path.join(base_repo, items[0])) else base_repo
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(project_path, item)
                if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                else: shutil.copy2(s, d)
            print(f"📦 [DIAMOND MERGE] Lógica de backend integrada de {base_repo}")
        except Exception as e:
            print("⚠️ Erro ao mesclar repositório base:", e)

    # Prioridade 2: UI do Cloner (sobrepõe assets de UI se necessário)
    if cloned_path and os.path.exists(cloned_path):
        try:
            for item in os.listdir(cloned_path):
                s = os.path.join(cloned_path, item)
                d = os.path.join(project_path, "static", item) if item.endswith((".html", ".css", ".js")) else os.path.join(project_path, item)
                os.makedirs(os.path.dirname(d), exist_ok=True)
                if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                else: shutil.copy2(s, d)
            print(f"🎨 [DIAMOND MERGE] UI de referência integrada de {cloned_path}")
        except Exception as e:
            print("⚠️ Erro ao mesclar UI clonada:", e)

    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "B", created)

    print(f"  ✅ App salvo em: {project_path}")
    return project_path


def _generate_readme(task: str, files: dict) -> str:
    return f"""# {task[:60]}

Aplicação web gerada automaticamente.

## Instalação e Execução

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Acesse: http://localhost:8000

## Estrutura
{chr(10).join(f"- {f}" for f in files.keys())}
"""


def _fallback_todo_app(task: str) -> str:
    """App Todo list simples como fallback garantido."""
    main_py = '''from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import uvicorn
import json, os

app = FastAPI(title="Task Manager")
TASKS_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f: return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f: json.dump(tasks, f)

HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Task Manager</title>
<style>
body{font-family:Inter,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:20px}
.container{max-width:700px;margin:0 auto}
h1{color:#38bdf8;font-size:2rem;margin-bottom:30px}
form{display:flex;gap:10px;margin-bottom:30px}
input{flex:1;padding:12px;background:#1e293b;border:2px solid #334155;border-radius:8px;color:#e2e8f0;font-size:1rem}
input:focus{outline:none;border-color:#38bdf8}
button{padding:12px 24px;background:#38bdf8;color:#0f172a;border:none;border-radius:8px;cursor:pointer;font-weight:700;font-size:1rem}
button:hover{background:#7dd3fc}
.task{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:16px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
.task-done{opacity:0.5;text-decoration:line-through}
.del-btn{background:#ef4444;color:white;border:none;border-radius:6px;padding:6px 12px;cursor:pointer}
.done-btn{background:#22c55e;color:white;border:none;border-radius:6px;padding:6px 12px;cursor:pointer;margin-right:8px}
.stats{background:#1e293b;border-radius:10px;padding:16px;margin-bottom:20px;border-left:4px solid #38bdf8}
</style></head>
<body><div class="container">
<h1>🤖 Task Manager</h1>
<div class="stats">📊 <strong>{{total}}</strong> tarefas | ✅ <strong>{{done}}</strong> concluídas</div>
<form method="post" action="/add">
  <input name="text" placeholder="Nova tarefa..." required autocomplete="off">
  <button type="submit">+ Adicionar</button>
</form>
{{tasks_html}}
</div></body></html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    tasks = load_tasks()
    tasks_html = ""
    for i, t in enumerate(tasks):
        cls = "task-done" if t.get("done") else ""
        tasks_html += f"""<div class="task">
          <span class="{cls}">{t["text"]}</span>
          <div>
            <form method="post" action="/done/{i}" style="display:inline">
              <button class="done-btn" type="submit">{"↩️" if t.get("done") else "✅"}</button>
            </form>
            <form method="post" action="/delete/{i}" style="display:inline">
              <button class="del-btn" type="submit">🗑️</button>
            </form>
          </div>
        </div>"""
    done = sum(1 for t in tasks if t.get("done"))
    html = HTML.replace("{{tasks_html}}", tasks_html or "<p style='color:#64748b'>Nenhuma tarefa ainda.</p>")
    html = html.replace("{{total}}", str(len(tasks))).replace("{{done}}", str(done))
    return html

@app.post("/add")
def add(request: Request, text: str = Form(...)):
    from fastapi.responses import RedirectResponse
    tasks = load_tasks()
    tasks.append({"text": text, "done": False})
    save_tasks(tasks)
    return RedirectResponse("/", status_code=303)

@app.post("/done/{idx}")
def toggle_done(idx: int):
    from fastapi.responses import RedirectResponse
    tasks = load_tasks()
    if 0 <= idx < len(tasks):
        tasks[idx]["done"] = not tasks[idx].get("done", False)
    save_tasks(tasks)
    return RedirectResponse("/", status_code=303)

@app.post("/delete/{idx}")
def delete(idx: int):
    from fastapi.responses import RedirectResponse
    tasks = load_tasks()
    if 0 <= idx < len(tasks):
        tasks.pop(idx)
    save_tasks(tasks)
    return RedirectResponse("/", status_code=303)

@app.get("/api/tasks")
def api_tasks(): return load_tasks()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    project_path = create_project_dir(task)
    files = {
        "main.py": main_py,
        "requirements.txt": "fastapi\nuvicorn\n",
        "README.md": f"# Task Manager\n\n{task}\n\n## Executar\n```bash\npip install -r requirements.txt\npython main.py\n```\n\nAcesse: http://localhost:8000\n"
    }
    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "B", created)
    return project_path