"""
API Principal — Antigravity Agent System v2.0
FastAPI com WebSocket streaming, CORS, e endpoints completos.
"""
import os
import asyncio
import sys
import uuid
import multiprocessing
import queue as py_queue
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configura multiprocessing para Windows
try:
    if multiprocessing.get_start_method() != 'spawn':
        multiprocessing.set_start_method('spawn', force=True)
except: pass

_active_processes = {} # task_id -> Process
_task_logs = {}
_active_tasks = {}

class StdoutRedirector:
    def __init__(self, queue):
        self.queue = queue
        self.terminal = sys.__stdout__ # Salva o terminal original

    def write(self, message):
        if message:
            # TEE: Escreve no terminal real (Gold Rule)
            self.terminal.write(message)
            self.terminal.flush()
            
            # Envia para a queue do Dashboard
            if message.strip():
                self.queue.put(message.strip())
    def flush(self):
        pass

def pipeline_worker(task_id, task_text, user_id, model, mode, log_queue, forced_agent=None, history=None):
    """Worker que roda em processo isolado para permitir interrupção real."""
    import sys
    
    # Fix UTF-8 for subprocess in Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Redireciona stdout para a queue de logs (Visualização Real-time no Dashboard)
    sys.stdout = StdoutRedirector(log_queue)
    
    try:
        # Import tardio para evitar lock circular
        from engine.pipeline import run_pipeline
        result = run_pipeline(
            task=task_text,
            user_id=user_id,
            model=model,
            task_id=task_id,
            log_queue=log_queue,
            forced_agent=forced_agent,
            history=history
        )
        log_queue.put({"__type__": "RESULT", "data": result})
    except Exception as e:
        log_queue.put({"__type__": "RESULT", "data": {"status": "failed", "error": str(e)}})

from engine.pipeline import cancel_diamond_task
from core.memory import get_stats
from core.workspace import list_projects, get_project
from core.llm import get_available_models, invalidate_model_cache, classify_model, CLOUD_CATALOG

# ===================================================
# APP CONFIG
# ===================================================
app = FastAPI(
    title="🐶 Bulldog AI",
    description="Sistema de agentes autônomos Bulldog — cria jogos, apps e scripts sob demanda.",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================================================
# SCHEMAS
# ===================================================
class RunRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = "fast"
    forced_agent: Optional[str] = None
    history: Optional[list] = []

class RunResponse(BaseModel):
    status: str
    route: Optional[str] = None
    agent: Optional[str] = None
    project_path: Optional[str] = None
    files: list[str] = []
    score: float = 0.0
    iterations: int = 0
    output: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = ""

# ===================================================
# TASK STORE (em memória — tasks em progresso)
# ===================================================
_active_tasks: dict[str, dict] = {}
_task_logs: dict[str, list[str]] = {}


# ===================================================
# ENDPOINTS PRINCIPAIS
# ===================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página inicial com documentação rápida."""
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content=_default_home_html(), status_code=200)


@app.get("/health")
async def health():
    """Health check — verifica se o sistema está online."""
    models = get_available_models()
    ollama_online = len(models) > 0

    return {
        "status": "healthy" if ollama_online else "degraded",
        "timestamp": datetime.now().isoformat(),
        "ollama_online": ollama_online,
        "available_models": models,
        "version": "2.0.0"
    }

# Mount assets properly (Gold Rule: Fix 404)
from fastapi.staticfiles import StaticFiles
app.mount("/assets", StaticFiles(directory="dashboard/assets"), name="assets")


@app.post("/run", response_model=RunResponse)
async def run(payload: RunRequest, background_tasks: BackgroundTasks):
    """
    Executa uma tarefa de forma síncrona.
    Para tarefas longas, use /run/async + WebSocket /ws/{task_id}.
    """
    if not payload.prompt or len(payload.prompt.strip()) < 3:
        raise HTTPException(status_code=400, detail="Prompt muito curto")

    from engine.pipeline import run_pipeline
    result = run_pipeline(
        task=payload.prompt.strip(),
        user_id=payload.user_id,
        model=payload.model,
        mode=payload.mode,
        task_id=str(uuid.uuid4()) # ID temporário para logs se for síncrono
    )

    return RunResponse(
        **result,
        timestamp=datetime.now().isoformat()
    )


@app.post("/run/async")
async def run_async(payload: RunRequest, background_tasks: BackgroundTasks):
    """
    Inicia tarefa em background e retorna task_id.
    Conecte-se via WebSocket /ws/{task_id} para receber logs em tempo real.
    """
    if not payload.prompt or len(payload.prompt.strip()) < 3:
        raise HTTPException(status_code=400, detail="Prompt muito curto")

    task_id = str(uuid.uuid4())
    _active_tasks[task_id] = {"status": "running", "prompt": payload.prompt}
    _task_logs[task_id] = []
    
    # Queue para comunicação entre processos
    log_queue = multiprocessing.Queue()
    
    # Inicia processo agressivo
    p = multiprocessing.Process(
        target=pipeline_worker,
        args=(task_id, payload.prompt.strip(), payload.user_id, payload.model, payload.mode, log_queue, payload.forced_agent, payload.history)
    )
    p.start()
    _active_processes[task_id] = p

    async def watch_process():
        """Consome a queue e atualiza o estado global da API."""
        try:
            while p.is_alive() or not log_queue.empty():
                try:
                    # Roda em thread para não bloquear o event loop
                    msg = await asyncio.to_thread(log_queue.get, timeout=0.1)
                    
                    if isinstance(msg, dict) and msg.get("__type__") == "RESULT":
                        result = msg["data"]
                        _active_tasks[task_id] = {**result, "status": result.get("status", "done")}
                    else:
                        _task_logs[task_id].append(str(msg))
                except py_queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                except Exception:
                    break
        finally:
            if task_id in _active_processes:
                del _active_processes[task_id]
            if _active_tasks[task_id].get("status") == "running":
                _active_tasks[task_id]["status"] = "done"

    background_tasks.add_task(watch_process)

    return {
        "task_id": task_id,
        "status": "running",
        "websocket_url": f"/ws/{task_id}",
        "poll_url": f"/tasks/{task_id}"
    }


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Consulta o status de uma tarefa assíncrona."""
    if task_id not in _active_tasks:
        raise HTTPException(status_code=404, detail="Task não encontrada")

    task = _active_tasks[task_id].copy()
    task["logs"] = _task_logs.get(task_id, [])
    return task


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancela uma tarefa killando o processo de forma fatal e agressiva."""
    # 1. Sinaliza Diamond Cancel (soft check)
    cancel_diamond_task(task_id)
    
    # 2. Kill Real (Hard check)
    if task_id in _active_processes:
        p = _active_processes[task_id]
        try:
            p.terminate() # Sinal SIGTERM
            await asyncio.sleep(0.2)
            if p.is_alive():
                p.kill() # Sinal SIGKILL (agressivo)
            p.join()
        except: pass
        
    if task_id in _active_tasks:
        _active_tasks[task_id]["status"] = "cancelled"
        _task_logs.setdefault(task_id, []).append("🛑 [DIAMOND KILL] Processo encerrado agressivamente pelo sistema.")
        return {"status": "cancelled"}
    
    raise HTTPException(status_code=404, detail="Task não encontrada")


@app.websocket("/ws/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str):
    """
    WebSocket para streaming de logs em tempo real.
    Fecha automaticamente quando a tarefa termina.
    """
    await websocket.accept()

    sent_idx = 0
    max_wait = 1200  # Diamond Timeout: 20 minutos máximo

    try:
        for _ in range(max_wait * 10):  # poll a cada 100ms
            # Envia novos logs
            logs = _task_logs.get(task_id, [])
            while sent_idx < len(logs):
                await websocket.send_json({"type": "log", "message": logs[sent_idx]})
                sent_idx += 1

            # Verifica se terminou
            task = _active_tasks.get(task_id, {})
            status = task.get("status", "running")

            if status != "running":
                await websocket.send_json({"type": "done", "result": task})
                break

            await asyncio.sleep(0.1)
        else:
            await websocket.send_json({"type": "timeout", "message": "Timeout de 5 minutos"})
    except Exception:
        # Desconexão silenciosa (Diamante) para evitar flood de logs
        pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# ===================================================
# PROJETOS
# ===================================================

@app.get("/projects")
async def list_all_projects():
    """Lista todos os projetos gerados na workspace."""
    return {"projects": list_projects()}


@app.get("/projects/{project_name}")
async def get_project_detail(project_name: str):
    """Retorna detalhes e conteúdo de um projeto específico."""
    workspace = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace")
    project_path = os.path.join(workspace, project_name)

    if not os.path.isdir(project_path):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return get_project(project_path)


@app.delete("/projects/{project_name}")
async def delete_project(project_name: str):
    """Exclui um projeto da workspace."""
    workspace = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace")
    project_path = os.path.join(workspace, project_name)

    if not os.path.isdir(project_path):
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    import shutil
    try:
        shutil.rmtree(project_path)
        return {"status": "deleted", "project": project_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar: {str(e)}")


# ===================================================
# SISTEMA
# ===================================================

@app.get("/stats")
async def stats():
    """Estatísticas do sistema de agentes."""
    return get_stats()


@app.get("/models")
async def models():
    """Lista modelos Ollama disponíveis detalhadamente + Catálogo Cloud."""
    invalidate_model_cache()
    available = list(get_available_models())
    
    # Mescla com o catálogo Diamond Cloud para visibilidade
    full_list = sorted(list(set(available + CLOUD_CATALOG)))
    
    models_detailed = []
    for m in full_list:
        category = classify_model(m)
        is_pulled = m in available
        models_detailed.append({
            "name": m,
            "category": category,
            "icon": "🌐" if category == "Diamond Cloud" else "🏠",
            "is_pulled": is_pulled
        })
        
    return {
        "models": models_detailed,
        "count": len(models_detailed)
    }


@app.post("/models/refresh")
async def refresh_models():
    """Força re-detecção dos modelos Ollama."""
    invalidate_model_cache()
    return {"models": get_available_models()}


# ===================================================
# HTML DASHBOARD (fallback se não existir /dashboard)
# ===================================================
def _default_home_html():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🐶 Bulldog AI</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', system-ui, sans-serif; background: #0a0f1e; color: #e2e8f0; min-height: 100vh; }
  .hero { background: linear-gradient(135deg, #0a0f1e 0%, #1a1f35 50%, #0d1b2a 100%); padding: 60px 20px; text-align: center; border-bottom: 1px solid #1e293b; }
  .badge { display: inline-block; background: #1e293b; color: #38bdf8; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 20px; border: 1px solid #334155; }
  .badge-icon { width:36px; height:36px; background: white; mask: url('assets/bulldog_white.png') no-repeat center; -webkit-mask: url('assets/bulldog_white.png') no-repeat center; mask-size: contain; -webkit-mask-size: contain; filter: drop-shadow(0 0 8px var(--accent-glow)); }
  h1 { font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; background: linear-gradient(135deg, #38bdf8, #818cf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 16px; }
  .subtitle { color: #94a3b8; font-size: 1.1rem; max-width: 600px; margin: 0 auto 40px; line-height: 1.6; }
  .container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; }
  .card { background: #111827; border: 1px solid #1e293b; border-radius: 16px; padding: 24px; margin-bottom: 24px; }
  .card-title { font-size: 1rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }
  .input-row { display: flex; gap: 12px; }
  textarea { flex: 1; background: #0f172a; border: 2px solid #1e293b; border-radius: 10px; padding: 14px; color: #e2e8f0; font-size: 1rem; font-family: inherit; resize: vertical; min-height: 80px; transition: border-color 0.2s; }
  textarea:focus { outline: none; border-color: #38bdf8; }
  .btn { padding: 14px 28px; border: none; border-radius: 10px; cursor: pointer; font-weight: 700; font-size: 1rem; transition: all 0.2s; white-space: nowrap; }
  .btn-primary { background: linear-gradient(135deg, #38bdf8, #818cf8); color: white; }
  .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(56, 189, 248, 0.3); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
  .logs { background: #0f172a; border-radius: 10px; padding: 16px; font-family: 'Fira Code', monospace; font-size: 0.85rem; max-height: 300px; overflow-y: auto; white-space: pre-wrap; color: #94a3b8; border: 1px solid #1e293b; display: none; }
  .result { display: none; }
  .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }
  .status-success { background: #052e16; color: #4ade80; border: 1px solid #166534; }
  .status-partial { background: #451a03; color: #fb923c; border: 1px solid #7c2d12; }
  .status-failed { background: #450a0a; color: #f87171; border: 1px solid #7f1d1d; }
  .files-list { list-style: none; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; margin-top: 12px; }
  .files-list li { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; color: #64748b; }
  .files-list li::before { content: "📄 "; }
  .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
  .stat-card { background: #111827; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; text-align: center; }
  .stat-number { font-size: 2rem; font-weight: 800; color: #38bdf8; }
  .stat-label { color: #64748b; font-size: 0.85rem; margin-top: 4px; }
  .route-badge { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
  .route-A { background: #1a1f35; color: #818cf8; }
  .route-B { background: #1a2535; color: #38bdf8; }
  .route-C { background: #1a2520; color: #4ade80; }
  .spinner { display: none; width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .examples { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
  .example-btn { background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 8px; padding: 6px 12px; font-size: 12px; cursor: pointer; transition: all 0.2s; }
  .example-btn:hover { background: #334155; color: #e2e8f0; }
  .path-display { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 0.9rem; color: #38bdf8; word-break: break-all; }
  a { color: #38bdf8; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .message { display: flex; gap: 16px; margin-bottom: 20px; }
  .avatar { width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0; }
  .avatar-ai { background: #38bdf8; }
  .msg-content { flex: 1; }
  .user-text { background: #1e293b; padding: 16px; border-radius: 12px; }
  .open-files-btn { background: #38bdf8; color: #0a0f1e; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }
</style>
</head>
<body>

<div class="hero">
  <div class="badge"><div class="badge-icon"></div> 🐶 Powered by Bulldog AI + Local GPU</div>
  <h1>🐶 Bulldog AI Agent</h1>
  <p class="subtitle">O sistema autônomo mais robusto do mundo. Criamos software industrial sob demanda — tudo rodando na sua máquina.</p>
</div>

<div class="container">

  <!-- MAIN FORM -->
  <div class="card">
    <div class="card-title">▶ Nova Tarefa</div>
    <div class="input-row">
      <textarea id="prompt" placeholder="Ex: Crie um jogo snake em Python... / Crie um dashboard de tarefas... / Crie um script que converte PDF para texto..."></textarea>
      <button class="btn btn-primary" id="runBtn" onclick="runTask()">
        🚀 Executar
      </button>
    </div>
    <div class="examples">
      <span style="color:#64748b;font-size:12px;align-self:center">Exemplos:</span>
      <div class="message" id="welcomeMsg">
        <div class="avatar avatar-ai" style="background: white; mask: url('assets/bulldog_white.png') no-repeat center; -webkit-mask: url('assets/bulldog_white.png') no-repeat center; mask-size: contain; -webkit-mask-size: contain;"></div>
        <div class="msg-content">
          <div class="user-text">
            <h2>Bem-vindo à Fábrica Bulldog AI</h2>
            <p style="color:var(--text-secondary); margin-top:8px">Olá, eu sou a Bulldog Frida. O sistema foi elevado ao nível <strong>Bulldog Elite</strong>. Gere código de alta performance com a força de um Bulldog.</p>
            <div style="display:flex; gap:12px; margin-top:20px; flex-wrap:wrap">
              <button class="open-files-btn" onclick="setPrompt('Crie um jogo Snake em HTML5 super polido com placar de pontos.')" style="margin:0; font-size:0.85rem">🐍 Jogo Snake</button>
              <button class="open-files-btn" onclick="setPrompt('Crie um script automotizado que lê um CSV e gera gráficos de evolução num arquivo PDF.')" style="margin:0; font-size:0.85rem">📊 Script de Dados</button>
              <button class="open-files-btn" onclick="setPrompt('Construa um app de gestão de tarefas em FastAPI com Kanban Board completo.')" style="margin:0; font-size:0.85rem">📝 App Kanban</button>
            </div>
          </div>
        </div>
      </div>
      <button class="example-btn" onclick="setPrompt('Crie um script que lista e organiza arquivos por extensão')">📁 Org. Arquivos</button>
      <button class="example-btn" onclick="setPrompt('Crie um jogo de plataforma 2D simples em pygame')">🎮 Plataforma 2D</button>
      <button class="example-btn" onclick="setPrompt('Crie uma calculadora web com histórico de operações')">🔢 Calculadora</button>
    </div>
  </div>

  <!-- LOGS -->
  <div class="card" id="logsCard" style="display:none">
    <div class="card-title">📋 Logs em Tempo Real</div>
    <div class="spinner" id="spinner"></div>
    <div class="logs" id="logs"></div>
  </div>

  <!-- RESULT -->
  <div class="card result" id="resultCard">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <div class="avatar avatar-ai" style="background: white; mask: url('assets/bulldog_white.png') no-repeat center; -webkit-mask: url('assets/bulldog_white.png') no-repeat center; mask-size: contain; -webkit-mask-size: contain;"></div>
        <span class="status-badge" id="statusBadge"></span>
      </div>
    </div>
    <div id="projectPath" class="path-display" style="margin-bottom:16px;display:none"></div>
    <div id="filesList"></div>
  </div>

  <div style="text-align:center;margin-top:30px;color:#334155;font-size:0.85rem">
    <a href="/docs" target="_blank">📚 API Docs</a> &nbsp;|&nbsp;
    <a href="/projects" target="_blank">📁 Projetos</a> &nbsp;|&nbsp;
    <a href="/health" target="_blank">💚 Status</a> &nbsp;|&nbsp;
    <a href="/models" target="_blank">🧠 Modelos</a>
  </div>
</div>

<script>
let ws = null;
let history = [];

function setPrompt(text) {
  document.getElementById('prompt').value = text;
  document.getElementById('prompt').focus();
}

async function runTask() {
  const prompt = document.getElementById('prompt').value.trim();
  if (!prompt) return;

  const btn = document.getElementById('runBtn');
  const logsCard = document.getElementById('logsCard');
  const logsEl = document.getElementById('logs');
  const spinner = document.getElementById('spinner');
  const resultCard = document.getElementById('resultCard');

  btn.disabled = true;
  btn.textContent = '⏳ Processando...';
  logsCard.style.display = 'block';
  logsEl.style.display = 'block';
  logsEl.textContent = '';
  resultCard.style.display = 'none';
  spinner.style.display = 'block';

  history.push({role: 'user', content: prompt});

  try {
    const startRes = await fetch('/run/async', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, history })
    });
    const startData = await startRes.json();
    const taskId = startData.task_id;

    addLog(`📋 Task ID: ${taskId}`);

    // Conecta WebSocket para logs em tempo real
    const wsUrl = `ws://${location.host}/ws/${taskId}`;
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'log') {
        addLog(data.message);
      } else if (data.type === 'done') {
        showResult(data.result);
        finalize(btn, spinner);
      } else if (data.type === 'timeout') {
        addLog('⏱ Timeout — verificando resultado...');
        pollResult(taskId, btn, spinner);
      }
    };

    ws.onerror = () => {
      addLog('⚠️ WebSocket indisponível — usando polling...');
      pollResult(taskId, btn, spinner);
    };

    ws.onclose = () => {};

  } catch (err) {
    addLog(`❌ Erro: ${err.message}`);
    finalize(btn, spinner);
  }
}

function pollResult(taskId, btn, spinner) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/tasks/${taskId}`);
      const data = await res.json();

      // Adiciona novos logs
      const logs = data.logs || [];
      const logsEl = document.getElementById('logs');
      const currentLines = logsEl.textContent.split('\n').length;
      if (logs.length > currentLines) {
        logs.slice(currentLines).forEach(addLog);
      }

      if (data.status !== 'running') {
        clearInterval(interval);
        showResult(data);
        finalize(btn, spinner);
      }
    } catch (e) {
      clearInterval(interval);
      finalize(btn, spinner);
    }
  }, 1000);
}

function addLog(msg) {
  const el = document.getElementById('logs');
  if (!el) return;
  el.textContent += msg + '\n';
  el.scrollTop = el.scrollHeight;
  
  const chatArea = document.getElementById('chatArea');
  if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
}

function showResult(result) {
  const card = document.getElementById('resultCard');
  const badge = document.getElementById('statusBadge');
  const pathEl = document.getElementById('projectPath');
  const filesEl = document.getElementById('filesList');
  const chatArea = document.getElementById('chatArea') || document.body;

  // ROUTE D / CHAT MESSAGE
  if (result.route === 'D' || result.message) {
    const aiMsg = document.createElement('div');
    aiMsg.className = 'message';
    aiMsg.innerHTML = `
      <div class="avatar avatar-ai">🐶</div>
      <div class="msg-content">
        <div class="bubble bubble-ai">
          ${new Remarkable().render(result.message || 'Tarefa Bulldog concluída.')}
        </div>
      </div>
    `;
    chatArea.appendChild(aiMsg);
    chatArea.scrollTop = chatArea.scrollHeight;
    return;
  }

  // PROJECT GENERATION (A/B/C)
  card.style.display = 'block';

  const statusMap = {
    'success': ['status-success', '✅ Sucesso Bulldog'],
    'partial': ['status-partial', '⚠️ Parcial'],
    'failed': ['status-failed', '❌ Falhou'],
  };
  const [cls, label] = statusMap[result.status] || ['', result.status];
  badge.className = `status-badge ${cls}`;
  badge.textContent = label;

  if (result.project_path) {
    pathEl.style.display = 'block';
    pathEl.textContent = '📁 ' + result.project_path;
  }

  if (result.files && result.files.length > 0) {
    filesEl.innerHTML = `<p style="color:#94a3b8;margin-bottom:8px;font-size:0.9rem">📂 ${result.files.length} arquivo(s) prontos:</p>
    <ul class="files-list">${result.files.map(f => `<li>${f}</li>`).join('')}</ul>`;
  }

  chatArea.scrollTop = chatArea.scrollHeight;
  loadStats();
}

function finalize(btn, spinner) {
  btn.disabled = false;
  btn.textContent = '🚀 Executar';
  spinner.style.display = 'none';
}

async function loadStats() {
  try {
    const res = await fetch('/stats');
    const data = await res.json();
    document.querySelector('#statTotal .stat-number').textContent = data.total_tasks || 0;
    document.querySelector('#statRate .stat-number').textContent = Math.round((data.success_rate || 0) * 100) + '%';
    document.querySelector('#statScore .stat-number').textContent = ((data.average_score || 0) * 100).toFixed(0) + '%';
  } catch (e) {}
}

// Carrega stats ao iniciar
loadStats();
</script>
</body>
</html>"""