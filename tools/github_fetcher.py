import requests
import os
import zipfile
import io
import requests

def search(query):
    """
    Busca repositórios no GitHub via API pública
    """

    url = f"https://api.github.com/search/repositories?q={query}&sort=stars"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        repos = []

        for item in data.get("items", [])[:5]:
            repos.append({
                "name": item["name"],
                "url": item["html_url"],
                "description": item["description"]
            })

        return repos

    except Exception as e:
        return []

BASE = "https://api.github.com/search/repositories"

def github_fetch(query):
    print(f"🔎 Query: {query}")

    url = f"{BASE}?q={query}&sort=stars&order=desc&per_page=10"

    headers = {
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("❌ Erro GitHub:", r.text)
        return []

    data = r.json()
    items = data.get("items", [])

    good_repos = []

    for item in items:
        stars = item.get("stargazers_count", 0)
        forks = item.get("forks_count", 0)

        # 🔥 FILTRO GOD
        if stars < 50:
            continue

        good_repos.append(item)

    folders = []

    os.makedirs("workspace", exist_ok=True)

    for repo in good_repos[:5]:
        name = repo["name"]
        zip_url = repo["html_url"] + "/archive/refs/heads/main.zip"

        print(f"⬇️ Baixando: {name} ⭐ {repo['stargazers_count']}")

        try:
            zip_data = requests.get(zip_url).content
            z = zipfile.ZipFile(io.BytesIO(zip_data))

            path = f"workspace/{name}"
            z.extractall(path)

            folders.append(path)

        except Exception as e:
            print("⚠️ Falha:", name, e)

    return folders