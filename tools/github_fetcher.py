import requests
import os
import zipfile
import io
import re
import time
from urllib.parse import quote

def _expand_diamond_query(query: str) -> str:
    """Expande a query priorizando termos técnicos em Inglês para o GitHub."""
    MAP = {
        "jogo de tiro": "shooter FPS",
        "tiro": "shooter",
        "primeira pessoa": "FPS",
        "plataforma": "platformer",
        "gestao": "ERP dashboard",
        "imposto": "tax invoice",
        "automacao": "automation python",
        "site": "web-application webapp",
        "loja": "ecommerce marketplace",
    }
    
    technical_keywords = []
    clean_query = query.lower()
    
    # 1. Mapeamento manual rápido
    for pt, en in MAP.items():
        if pt in clean_query:
            technical_keywords.append(en)
            
    # 2. Diamond LLM Expander (Foco em Inglês Técnico)
    try:
        from core.llm import ask
        # Timeout estendido e prompt focado em extração de keywords
        p = f"Convert this task into a PURE TECHNICAL ENGLISH GitHub search query (max 6 words, no prose): {query}"
        res = ask("DiamondExpander", p, model="llama3.1:8b", timeout=45)
        if res:
            # Limpa lixo da resposta
            clean_res = re.sub(r'["\.\?]', '', res).strip()
            if len(clean_res) > 3:
                technical_keywords.append(clean_res)
    except: pass
    
    # Se falhou tudo, usa a original truncada
    if not technical_keywords:
        return query[:200]

    # Une tudo e limita a 250 (GitHub threshold)
    final_query = " ".join(technical_keywords)
    if len(final_query) > 250:
        final_query = final_query[:250]
        
    return final_query

def github_fetch(query):
    import re
    print(f"🔎 [DIAMOND SEARCH] Analisando: {query[:100]}...")
    
    expanded_query = _expand_diamond_query(query)
    
    def try_search(q):
        print(f"🔎 Buscando no GitHub: '{q}'")
        url = "https://api.github.com/search/repositories"
        params = {
            "q": q[:250], # Truncação fatal
            "sort": "stars",
            "order": "desc",
            "per_page": 3
        }
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                return response.json().get("items", [])
            elif response.status_code == 422:
                print("⚠️ Query muito complexa para o GitHub, tentando simplificar...")
                return []
        except: return []
        return []

    # Tentativa 1: Query Expandida
    items = try_search(expanded_query)
    
    # Tentativa 2: Caso falhe, tenta apenas keywords técnicos (Fall-back)
    if not items and len(query.split()) > 3:
        print("💡 Tentando busca simplificada (English Keywords Only)...")
        simple_query = re.sub(r'[^\w\s]', '', query) # Remove lixo
        words = [w for w in simple_query.split() if len(w) > 3]
        fallback_query = " ".join(words[:5]) + " awesome boilerplate"
        items = try_search(fallback_query)

    print("📦 Repos encontrados:", len(items))

    base_folder = "github_projects"
    os.makedirs(base_folder, exist_ok=True)
    folders = []

    for item in items:
        repo_name = item.get("name", "repo_sem_nome")
        owner = item.get("owner", {}).get("login", "")
        # ZIPURL manual (100% confiável)
        zip_url = f"https://api.github.com/repos/{owner}/{repo_name}/zipball"
        folder = os.path.join(base_folder, repo_name)
        
        try:
            print(f"📥 Baixando {repo_name}...")
            r = requests.get(zip_url, timeout=30)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    z.extractall(base_folder)
                    # O GitHub zipa com uma pasta raiz nomeada repo-owner-hash
                    real_folder = [d for d in os.listdir(base_folder) if d.startswith(f"{owner}-{repo_name}") or d.startswith(f"{repo_name}")]
                    if real_folder:
                        folders.append(os.path.join(base_folder, real_folder[0]))
        except: pass
        
    if folders:
        print(f"🎉 Download concluído! {len(folders)} repositório(s) prontos na base de conhecimento.")
    else:
        print("⚠️  Busca finalizada: Nenhum novo repositório baixado.")
    
    return folders

def search_local_knowledge(query: str) -> str:
    """Busca em projetos já baixados localmente (Knowledge Base)."""
    import os, re
    base_folder = "github_projects"
    if not os.path.isdir(base_folder):
        return ""

    print(f"📚 [LOCAL KB] Consultando base de conhecimento para: {query[:50]}...")
    keywords = [w.lower() for w in re.sub(r'[^\w\s]', '', query).split() if len(w) > 3]
    results = []

    try:
        for root, _, files in os.walk(base_folder):
            for fname in files:
                # Prioriza .py e .md técnicos. Ignora .txt genéricos que podem ser lixo (dicionários)
                if fname.endswith((".py", ".md")) or (fname.endswith(".txt") and "manual" in fname.lower()):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            # Lê uma amostra para ver se não é uma lista gigante de palavras (dicionário)
                            sample = f.read(2000)
                            if len(sample.split()) > 100 and sum(1 for line in sample.splitlines() if len(line.split()) == 1) / len(sample.splitlines()) > 0.8:
                                # Parece um dicionário (1 palavra por linha), ignora
                                continue
                            
                            content = sample + f.read() # Resto do arquivo
                            score = sum(1 for kw in keywords if kw in content.lower())
                            
                            # Peso extra para arquivos Python (Lógica real)
                            if fname.endswith(".py"): score *= 2

                            if score > 0:
                                rel_path = os.path.relpath(fpath, base_folder)
                                results.append((score, rel_path, content[:1000]))
                    except: continue
        
        results.sort(key=lambda x: x[0], reverse=True)
        top = results[:3]
        if not top: return ""

        kb_content = "\n=== CONHECIMENTO LOCAL ENCONTRADO ===\n"
        for score, path, text in top:
            kb_content += f"Arquivo: {path} (relevancia: {score})\nTrecho: {text}\n---\n"
        
        print(f"✅ [KB] Encontrados {len(top)} documentos relevantes localmente.")
        return kb_content
    except Exception as e:
        print(f"⚠️ Erro na busca local: {e}")
        return ""


def github_search_agents(query: str) -> list[dict]:
    """Busca definições de agentes (Modular Agents) no GitHub."""
    import requests, re
    print(f"🔎 [AGENT SEARCH] Caçando agentes especializados para: {query}...")
    
    agent_query = f'{query} "Agent(role=" OR "Agent(goal=" language:python'
    url = "https://api.github.com/search/code"
    params = {"q": agent_query, "per_page": 5}
    
    agents_found = []
    try:
        response = requests.get(url, params=params, timeout=20)
        if response.status_code == 200:
            items = response.json().get("items", [])
            for item in items:
                repo = item.get("repository", {}).get("full_name", "")
                f_url = item.get("html_url", "").replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                r = requests.get(f_url, timeout=10)
                if r.status_code == 200:
                    content = r.text
                    role_match = re.search(r'role\s*=\s*[\'"](.*?) [\'"]', content)
                    goal_match = re.search(r'goal\s*=\s*[\'"](.*?) [\'"]', content)
                    if role_match or goal_match:
                        agents_found.append({
                            "repo": repo,
                            "role": role_match.group(1) if role_match else "Especialista",
                            "goal": goal_match.group(1) if goal_match else query,
                            "content": content[:2000]
                        })
        print(f"🤖 [AGENT SEARCH] Agentes encontrados: {len(agents_found)}")
        return agents_found
    except Exception as e:
        print(f"⚠️ Falha na busca de agentes: {e}")
        return []
