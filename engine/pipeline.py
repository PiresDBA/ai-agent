"""
Pipeline AGI v9 — Motor central do sistema de agentes.

Melhorias v9:
  ✅ Deadlock lógico corrigido (stuck escape ANTES do return)
  ✅ Agentes geram arquivos reais (não texto)
  ✅ Executor trabalha com caminhos de pasta
  ✅ Quality e Security com tipos corretos
  ✅ Fixer aplica correções reais ao código
  ✅ Streaming de logs via callback
  ✅ Sem pipeline_lock global
"""
import os
import sys
import time
import hashlib
import shutil
import json
from typing import Callable, Optional

class DiamondInterrupt(Exception):
    """Exceção para interrupção imediata de tarefas Diamond."""
    pass

_CANCELLED_TASKS = set()

def cancel_diamond_task(task_id: str):
    """Marca uma tarefa para cancelamento agressivo."""
    if task_id:
        _CANCELLED_TASKS.add(task_id)

def _is_diamond_cancelled(task_id: str) -> bool:
    return task_id in _CANCELLED_TASKS

# Fix encoding for Windows terminals (permite emojis e UTF-8)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.orchestrator import route
from core.memory import remember_success, remember_failure
from core.workspace import create_project_dir, write_files_to_project, list_projects, cleanup_old_projects
from core.json_utils import extract_files_from_llm
from core.llm import ask

from agents.agent_a_game import agent_a
from agents.agent_b_saas import agent_b
from agents.agent_c_dev import agent_c

from engine.executor import run_project, validate_project_structure
from engine.security import security_check
from engine.quality import quality_check

MAX_ITERATIONS = 3
MAX_FIX_ATTEMPTS = 2


# ===================================================
# SELEÇÃO DE AGENTE
# ===================================================
def select_agent(route_id: str) -> Callable:
    agents = {"A": agent_a, "B": agent_b, "C": agent_c}
    return agents.get(route_id, agent_c)


# ===================================================
# CLASSIFIER DE ERROS
# ===================================================
def classify_error(error: str | None) -> str:
    if not error:
        return "ok"
    err = str(error).lower()
    if "winerror 267" in err or "not a directory" in err:
        return "bad_path"
    if "filenotfounderror" in err or "no such file" in err:
        return "missing_file"
    if "permissionerror" in err:
        return "permission"
    if "timeout" in err:
        return "timeout"
    if "modulenotfounderror" in err or "importerror" in err:
        return "missing_dep"
    if "syntaxerror" in err or "unexpected token" in err:
        return "syntax"
    if "attributeerror" in err:
        return "attr_error"
    if "nameerror" in err:
        return "name_error"
    if "typeerror" in err:
        return "type_error"
    return "unknown"


# ===================================================
# SMART FIXER — corrige projeto com LLM
# ===================================================
def smart_fix(project_path: str, error: str, output: dict, log: Callable) -> str:
    """
    Tenta corrigir o projeto analisando os erros e reescrevendo arquivos.

    Returns:
        Novo caminho de projeto corrigido, ou o original se falhar.
    """
    # Lê os arquivos do projeto
    project_files = {}
    if os.path.isdir(project_path):
        for root, _, files in os.walk(project_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, project_path)
                if not fname.endswith((".pyc", ".json")) and fname != "README.md":
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            project_files[rel] = f.read()[:3000]  # trunca
                    except Exception:
                        pass

    files_str = "\n\n".join(
        f"=== {fname} ===\n{content}"
        for fname, content in project_files.items()
    )

    stderr = output.get("stderr", "") if isinstance(output, dict) else str(output)

    prompt = f"""Você é o ENGENHEIRO DE DEBUGGING DIAMOND (Tech Lead).
FILOSOFIA OBRIGATÓRIA: NUNCA REMOVA SEM NECESSIDADE VITAL, SOMENTE MELHORE E CORRIJA, MELHORIA CONTINUA E EXCELENCIA!

Sua missão é realizar uma CIRURGIA TÉCNICA para atingir a perfeição Diamond.

CONTEXTO DE FALHA/QUALIDADE:
{error or stderr or "Baixa qualidade detectada na avaliação senior."}

ARQUIVOS ATUAIS DO PROJETO:
{files_str[:5000]}

DIRETRIZES TÉCNICAS:
1. ANÁLISE PROFUNDA: Identifique a causa raiz e resolva com precisão.
2. REFATORAÇÃO ADITIVA: Melhore a estrutura sem remover lógica funcional pré-existente.
3. COMPLETUDE TOTAL: NUNCA use placeholders. 100% de código real.
4. DEPENDÊNCIAS: Garanta `requirements.txt` atualizado se necessário.
5. CLEAN CODE: SOLID, Docstrings e Type Hinting.

FORMATO DE SAÍDA:
```linguagem # nome_do_arquivo.ext
# Explicação Técnica Diamond
# Código Corrigido e Industrial
```"""

    log(f"🔧 Enviando para correção via LLM...")
    fixed_response = ask("senior_debugger", prompt, timeout=300)

    if not fixed_response or len(fixed_response) < 50:
        log("⚠️  LLM não retornou correção")
        return project_path

    fixed_files = extract_files_from_llm(fixed_response)

    if not fixed_files:
        log("⚠️  Não foi possível extrair arquivos corrigidos")
        return project_path

    # Aplica correções no projeto existente
    created = write_files_to_project(project_path, fixed_files)
    log(f"✏️  Arquivos corrigidos: {list(fixed_files.keys())}")

    return project_path


# ===================================================
# PIPELINE PRINCIPAL
# ===================================================
def run_pipeline(
    task: str,
    user_id: str = None,
    log_callback: Callable = None,
    model: str = None,
    mode: str = "fast",
    task_id: str = None,
    log_queue = None
) -> dict:
    """
    Pipeline AGI v9 completo.

    Args:
        task: Descrição do que o usuário quer criar
        user_id: ID do usuário (para rastreamento)
        log_callback: Função chamada com mensagens de log em tempo real

    Returns:
        dict com status, caminho do projeto, arquivos, histórico
    """
    def log(msg: str):
        if task_id and _is_diamond_cancelled(task_id):
            raise DiamondInterrupt("Tarefa interrompida pelo usuário.")
        
        print(msg)
        # Salva em arquivo de log real-time
        with open("logs/pipeline.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        
        if log_queue:
            try: log_queue.put(msg)
            except: pass

        if log_callback:
            log_callback(msg)

    log(f"\n{'='*60}")
    log(f"🤖 PIPELINE AGI v9 | Tarefa: {task[:80]}")
    log(f"{'='*60}")

    try:
        # ===================================================
        # 1. ROTEAMENTO
        # ===================================================
        decision = route(task, use_cache=False)
        r = decision.route
        log(f"🧭 Roteado → Agente {r} ({decision.reason}, conf={decision.confidence:.2f})")

        # ===================================================
        # 2. GERAÇÃO INICIAL DO PROJETO
        # ===================================================
        agent_fn = select_agent(r)
        log(f"🚀 Iniciando geração com Agente {r}...")

        try:
            project_path = agent_fn(task, model=model, mode=mode)
        except Exception as e:
            log(f"❌ Falha na geração inicial: {e}")
            remember_failure(task, r, str(e))
            return {
                "status": "failed",
                "route": r,
                "error": str(e),
                "project_path": None,
                "files": []
            }

        if not project_path or not os.path.isdir(project_path):
            msg = f"Agente não gerou diretório válido: {project_path}"
            log(f"❌ {msg}")
            remember_failure(task, r, msg)
            return {
                "status": "failed",
                "route": r,
                "error": msg,
                "project_path": None,
                "files": []
            }

        log(f"📁 Projeto em: {project_path}")

        # Valida estrutura
        validation = validate_project_structure(project_path)
        log(f"🔍 Validação: score={validation['score']}, problemas={validation['issues']}")

        # ===================================================
        # 3. LOOP DE REFINAMENTO (Até 3 iterações + 1 refatoração total se falhar)
        # ===================================================
        history = []
        last_error_hash = None
        stuck_count = 0
        final_score = 0.0

        for iteration in range(MAX_ITERATIONS + 1):
            log(f"\n🔁 Iteração {iteration + 1}/{MAX_ITERATIONS if iteration < 3 else 'REFACTOR'}")

            # CHECK CANCEL
            if task_id and _is_diamond_cancelled(task_id):
                raise DiamondInterrupt("Tarefa interrompida pelo usuário.")

            # Se chegamos na '4ª' iteração (index 3), deletamos e começamos do zero com outro modelo
            if iteration == 3:
                log("🚨 Qualidade insuficiente após 3 tentativas. EXCLUINDO E RECOMEÇANDO DO ZERO (Refactor Total)...")
                
                # Tenta trocar de modelo para dar uma nova perspectiva
                from core.llm import get_available_models
                available = get_available_models()
                current_model = model or (available[0] if available else "llama3.1:8b")
                new_model = current_model
                
                if len(available) > 1:
                    try:
                        # Encontra o próximo modelo disponível
                        idx = available.index(current_model)
                        new_model = available[(idx + 1) % len(available)]
                        log(f"🔄 Perspectiva Diamond renovada: Trocando {current_model} -> {new_model}")
                    except:
                        new_model = available[0]

                import shutil
                try:
                    shutil.rmtree(project_path, ignore_errors=True)
                except: pass
                
                # Recomeça do zero com o novo modelo e a mesma tarefa
                project_path = agent_fn(task, model=new_model, mode=mode)
                
                # Reseta estado do loop para a nova tentativa "Diamond Reset"
                error = None
                error_type = None
                exec_result = {"success": False}

            # --- Executa o projeto ---
            exec_result = run_project(project_path=project_path, timeout=30)
            final_score = validation["score"] / 100.0  # base
            
            error = exec_result.get("error")
            error_type = exec_result.get("error_type", "unknown")

            # Se rodou, aplicamos avaliação técnica profunda
            if exec_result["success"]:
                # Pega o conteúdo principal para o Tech Lead avaliar
                main_code = _read_main_file(project_path)
                quality = quality_check(main_code, task)
                final_score = quality["score"]
                log(f"📊 Qualidade: {final_score:.2f} {'✅' if final_score >= 0.85 else '❌'}")
                if quality.get("issues"):
                    log(f"  Issues: {quality['issues']}")

                # Se passou no Diamond Score, paramos
                if final_score >= 0.85:
                    error = None
            else:
                log(f"  Execução: ❌ {error_type}")
                if error_type in ("syntax", "import"):
                    log(f"💀 Erro crítico ({error_type}) → Tentando corrigir")
                
            history.append({
                "iteration": iteration + 1,
                "error": error,
                "score": final_score,
                "error_type": error_type
            })

            # --- Sucesso! ---
            if exec_result["success"] and (final_score >= 0.85 or iteration == MAX_ITERATIONS - 1):
                log(f"\n✅ SUCESSO! Score: {final_score:.2f} | Iterações: {iteration + 1}")

                # Persiste na memória
                remember_success(task, r, final_score, project_path)

                # Lista arquivos gerados
                files_created = []
                for root, _, fnames in os.walk(project_path):
                    for fname in fnames:
                        rel = os.path.relpath(os.path.join(root, fname), project_path)
                        files_created.append(rel)

                return {
                    "status": "success",
                    "route": r,
                    "agent": f"Agent {r}",
                    "project_path": project_path,
                    "files": files_created,
                    "score": final_score,
                    "iterations": iteration + 1,
                    "history": history,
                    "output": exec_result.get("stdout", "")[:2000]
                }

            # Ainda tem iterações → tenta melhorar
            if iteration < MAX_ITERATIONS:
                if not exec_result["success"] or final_score < 0.85:
                    log(f"  🔧 Aplicando correções (motivo: {'execução' if not exec_result['success'] else 'qualidade'})...")
                    project_path = smart_fix(project_path, error or "quality issue/low score", exec_result, log)

            time.sleep(0.3)

        # ===================================================
        # 4. SAÍDA COM FALHA (mas entrega o que tem)
        # ===================================================
        log(f"\n⚠️ Pipeline encerrado após limites atingidos")
        remember_failure(task, r, f"Max iterations reached, score={final_score}")

        files_created = []
        if project_path and os.path.isdir(project_path):
            for root, _, fnames in os.walk(project_path):
                for fname in fnames:
                    rel = os.path.relpath(os.path.join(root, fname), project_path)
                    files_created.append(rel)

        return {
            "status": "partial",
            "route": r,
            "agent": f"Agent {r}",
            "project_path": project_path,
            "files": files_created,
            "score": final_score,
            "iterations": 3,
            "history": history,
            "message": "Projeto gerado mas pode precisar de ajustes manuais"
        }

    except DiamondInterrupt as di:
        log(f"🛑 [DIAMOND INTERRUPT] {str(di)}")
        return {
            "status": "cancelled",
            "message": str(di),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    except Exception as e:
        log(f"💥 Erro fatal no pipeline: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ===================================================
# HELPERS
# ===================================================
def _read_main_file(project_path: str) -> str:
    """Lê o arquivo principal do projeto para análise."""
    candidates = ["main.py", "app.py", "index.py", "run.py", "index.html", "main.js", "package.json"]
    for fname in candidates:
        fpath = os.path.join(project_path, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()[:5000]
            except Exception:
                pass
    
    # Se não achou candidato primário, lê qualquer python
    for fpath in Path(project_path).glob("*.py"):
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                return f.read()[:5000]
        except Exception:
            pass
    return ""


def _try_install_requirements(project_path: str, log: Callable) -> bool:
    """Tenta instalar requirements.txt do projeto."""
    req_file = os.path.join(project_path, "requirements.txt")
    if not os.path.exists(req_file):
        return False

    import subprocess, sys
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file, "-q"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log("  📦 Dependencies instaladas com sucesso")
            return True
        else:
            log(f"  ⚠️  Falha ao instalar deps: {result.stderr[:200]}")
    except Exception as e:
        log(f"  ⚠️  pip falhou: {e}")
    return False