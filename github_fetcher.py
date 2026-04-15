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
        
    print("🎉 Download concluído!")
    return folders