"""
Agent C — Dev / Automation Specialist
Especializado em scripts, automação, processamento de dados e ferramentas CLI.
"""
from core.llm import ask
from core.json_utils import extract_files_from_llm
from core.workspace import create_project_dir, write_files_to_project, save_project_manifest


def agent_c(task: str, model: str = None, mode: str = "fast") -> str:
    """
    Gera scripts e ferramentas de automação funcionais.

    Returns:
        Caminho da pasta do projeto gerado
    """
    print(f"⚙️ [DEV AGENT] Criando automação: {task[:60]}...")

    # 3. KNOWLEDGE & FETCH: Busca de inteligência
    kb_context = ""
    external_agents = []
    try:
        from tools.github_fetcher import search_local_knowledge, github_search_agents
        # 3.1. Busca no Conhecimento Local (KB)
        kb_context = search_local_knowledge(task)
        # 3.2. Busca por Agentes Modulares no GitHub (PRO)
        external_agents = github_search_agents(task)
    except Exception as e:
        print("⚠️ Erro ao buscar conhecimento:", e)

    agent_context = ""
    if external_agents:
        agent_context = "\n=== AGENTES ESPECIALISTAS ENCONTRADOS (REFERÊNCIA) ===\n"
        for a in external_agents[:2]:
            agent_context += f"Agente de {a['repo']}: Role={a['role']}, Goal={a['goal']}\n"

    prompt = f"""IDENTIDADE:
Você é o Automation Agent, um agente especialista em automação de processos. Sua função é criar fluxos automáticos, scripts, integrações entre sistemas, pipelines de dados e bots. Você pensa como um engenheiro de dados e DevOps focado em eficiência.

{kb_context if kb_context else ""}
{agent_context if agent_context else ""}

REGRAS DO QUE VOCÊ PODE FAZER:
- Criar scripts de automação em Python, Node.js, Bash
- Integrar sistemas via APIs, Webhooks e filas de mensagem
- Criar pipelines de dados (ETL: extração, transformação, carga)
- Automatizar tarefas repetitivas (arquivos, emails, formulários, relatórios)
- Criar bots para Telegram, WhatsApp, Slack, Discord
- Configurar agendamento de tarefas (cron jobs, schedulers)
- Criar workflows em ferramentas como n8n, Make, Zapier (via código ou instrução)
- Monitorar processos e gerar alertas automáticos
- Criar scrapers e coletores de dados

REGRAS DO QUE VOCÊ NÃO PODE FAZER:
- NÃO criar interfaces visuais de aplicativo (telas, botões, UI)
- NÃO criar lógica de jogos
- NÃO responder como assistente de chat genérico
- NÃO criar automações sem validar a segurança e os riscos primeiro
- NÃO executar scripts destrutivos sem confirmação explícita do usuário
- NÃO executar tarefas que pertençam a outros agentes

PROTOCOLO DE EXECUÇÃO OBRIGATÓRIO:
1. Antes de qualquer código, mapeie: entrada de dados → processamento → saída esperada
2. Identifique e documente todos os pontos de falha possíveis
3. Implemente tratamento de erro em TODOS os pontos críticos
4. Teste com dados fictícios antes de dados reais
5. Ao finalizar, verifique: (a) o que acontece se a fonte de dados falhar? (b) o processo pode ser revertido? (c) há dados sensíveis expostos?

PROTOCOLO DE SEGURANÇA (OBRIGATÓRIO):
- Nunca exponha credenciais, tokens ou senhas no código
- Sempre use variáveis de ambiente para dados sensíveis
- Sempre valide e sanitize dados de entrada
- Sempre implemente logs de execução

PROTOCOLO DE FALHA:
- Se a automação puder causar dano irreversível: pause e confirme com o usuário
- Se falhar: retorne o erro completo + causa + solução sugerida
- NUNCA silencia erros. NUNCA continua após falha crítica sem confirmação.

SAÍDA PADRÃO:
Sempre entregue: Diagrama do fluxo (texto) → Código com logs → Variáveis de ambiente necessárias → Como testar → Riscos conhecidos

TAREFA ATUAL: {task}"""

    # 4. DIAMOND TRIAGE: Avalia se a tarefa é simples (Relatório/Informação) ou complexa (Projeto)
    triage_prompt = f"Analyze if this task is a 'simple_information_report' or a 'complex_automation_project': {task}\nRespond ONLY 'simple' or 'complex'."
    is_simple = False
    try:
        triage_res = ask("DiamondTriage", triage_prompt, model="llama3.2:3b", timeout=15).lower()
        if "simple" in triage_res:
            is_simple = True
            print("💡 [FAST TRACK] Tarefa identificada como simples. Respondendo sem orquestração pesada...")
    except: pass

    if is_simple:
        # Responde direto (Fast-Track)
        response = ask("dev_engineer", prompt, model=model, timeout=120)
    else:
        # Tenta usar CrewAI para orquestração de 2 agentes (Lead + Developer)
        try:
            from core.crew_factory import run_diamond_crew
            print("🤝 [DIAMOND CREW] Iniciando colaboração de elite (2 Agentes)...")
            response = run_diamond_crew(f"Create an automation script following these rules: {prompt}", model_name=model)
        except Exception as e:
            print(f"⚠️ CrewAI não disponível ou falhou ({e}), usando agente único...")
            response = ask("dev_engineer", prompt, model=model, timeout=180)

    if not response or len(response) < 50:
        return _fallback_script(task)

    files = extract_files_from_llm(response)

    if not files or not any(files.values()):
        # Tenta usar resposta inteira como script Python
        import re
        code_match = re.search(r"```(?:python)?\n(.*?)```", response, re.DOTALL)
        if code_match:
            files = {"main.py": code_match.group(1).strip()}
        else:
            return _fallback_script(task)

    if "requirements.txt" not in files:
        files["requirements.txt"] = "# Nenhuma dependência externa necessária\n"

    if "manual.md" not in files:
        files["manual.md"] = f"# {task[:50]}\n\nScript gerado automaticamente.\n\n## Executar\n```bash\npython main.py\n```\n"

    project_path = create_project_dir(task)
    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "C", created)

    print(f"  ✅ Script salvo em: {project_path}")
    return project_path


def _fallback_script(task: str) -> str:
    """Script de sistema de arquivos como fallback."""
    script = f'''#!/usr/bin/env python3
"""
Script gerado para: {task}
"""
import os
import json
from pathlib import Path
from datetime import datetime

def main():
    print(f"🤖 Executando: {task[:60]}")
    print(f"📅 Data: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print(f"📁 Diretório: {{os.getcwd()}}")

    # Exemplo: lista arquivos do diretório atual
    files = list(Path(".").iterdir())
    print(f"\\n📂 Arquivos encontrados: {{len(files)}}")
    for f in sorted(files)[:20]:
        size = f.stat().st_size if f.is_file() else 0
        print(f"  {{\'📄\' if f.is_file() else \'📁\'}} {{f.name}} {{f\'({{size}} bytes)\' if f.is_file() else \'\'}}")

    print("\\n✅ Script executado com sucesso!")

if __name__ == "__main__":
    main()
'''
    project_path = create_project_dir(task)
    files = {
        "main.py": script,
        "requirements.txt": "# Sem dependências externas\n",
        "README.md": f"# Script\n\n{task}\n\n## Executar\n```bash\npython main.py\n```\n"
    }
    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "C", created)
    return project_path