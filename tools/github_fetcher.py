"""
GitHub Fetcher — Busca repositórios relevantes no GitHub.
"""
import requests
import os
import zipfile
import io
from urllib.parse import quote

GITHUB_API = "https://api.github.com/search/repositories"
WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace")

def _translate_diamond(query: str) -> str:
    """Expande a query para termos técnicos em inglês (Diamond Expander)."""
    # Mapeamento rápido para termos comuns (latência zero)
    MAPPING = {
        "jogo de tiro": "shooter FPS game",
        "tiro": "shooter",
        "primeira pessoa": "FPS",
        "terceira pessoa": "TPS",
        "plataforma": "platformer",
        "corrida": "racing",
        "luta": "fighting",
        "gestao": "management ERP dashboard",
        "imposto": "tax invoice finance",
        "automacao": "automation scripts bot",
        "rastreador": "tracker crawler scraper",
        "site": "web application site",
        "loja": "ecommerce store shopify",
        "banco de dados": "database sql nosql",
        "contabilidade": "accounting ledger finance",
        "relatorio": "reporting dashboard analytics",
    }
    
    expanded = query.lower()
    for pt, en in MAPPING.items():
        if pt in expanded:
            expanded += " " + en
            
    # Usa LLM rápida para expansão semântica profunda se for complexo
    if len(query.split()) > 3:
        try:
            from core.llm import ask
            prompt = f"Convert this search into international English technical keywords for GitHub: {query}\nKeywords:"
            # Timeout curto para manter performance Diamond
            llm_keywords = ask("DiamondExpander", prompt, model="llama3.2:3b", timeout=20)
            if llm_keywords and len(llm_keywords) > 2:
                expanded = f"{expanded} {llm_keywords}"
        except: pass
        
    return expanded


def search(query: str, limit: int = 5) -> list[dict]:
    """
    Busca repositórios no GitHub via API pública com expansão Diamond.

    Returns:
        Lista de dicts com {name, url, description, stars}
    """
    try:
        translated_query = _translate_diamond(query)
        print(f"🔍 Diamond GitHub Search: '{query}' -> '{translated_query}'")
        
        url = f"{GITHUB_API}?q={quote(translated_query)}&sort=stars&order=desc&per_page={limit}"
        response = requests.get(url, timeout=10, headers={"Accept": "application/vnd.github+json"})
        response.raise_for_status()
        data = response.json()

        repos = []
        for item in data.get("items", [])[:limit]:
            repos.append({
                "name": item["name"],
                "url": item["html_url"],
                "description": item.get("description") or "",
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "Unknown"
            })

        return repos

    except Exception as e:
        print(f"⚠️ GitHub search falhou: {e}")
        return []


def github_fetch(query: str, min_stars: int = 10) -> list[str]:
    """
    Busca e baixa repositórios relevantes do GitHub.

    Returns:
        Lista de caminhos locais onde os repos foram extraídos
    """
    repos = search(query, limit=10)
    repos = [r for r in repos if r.get("stars", 0) >= min_stars]

    if not repos:
        print(f"⚠️ Nenhum repositório encontrado para: {query}")
        return []

    os.makedirs(WORKSPACE, exist_ok=True)
    folders = []

    for repo in repos[:3]:  # máximo 3 downloads
        name = repo["name"]
        zip_url = f"{repo['url']}/archive/refs/heads/main.zip"

        print(f"⬇️ Baixando: {name} (⭐ {repo['stars']})")

        # Tenta branch main, depois master
        for branch in ["main", "master"]:
            zip_url = f"{repo['url']}/archive/refs/heads/{branch}.zip"
            try:
                r = requests.get(zip_url, timeout=30)  # timeout adicionado
                if r.status_code == 200:
                    z = zipfile.ZipFile(io.BytesIO(r.content))
                    path = os.path.join(WORKSPACE, name)
                    os.makedirs(path, exist_ok=True)
                    z.extractall(path)
                    folders.append(path)
                    print(f"  ✅ {name} extraído em {path}")
                    break
            except Exception as e:
                print(f"  ⚠️ Branch {branch} falhou: {e}")

    return folders