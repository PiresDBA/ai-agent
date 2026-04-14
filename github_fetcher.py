import requests
import os
import zipfile
import io

def github_fetch(query):
    print("🔎 Buscando no GitHub...")

    url = "https://api.github.com/search/repositories"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 3
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("❌ Erro API GitHub:", response.status_code)
        print(response.text)
        return []

    data = response.json()

    items = data.get("items", [])
    print("📦 Repos encontrados:", len(items))

    base_folder = "github_projects"
    os.makedirs(base_folder, exist_ok=True)

    folders = []

    for item in items:
        repo_name = item.get("name", "repo_sem_nome")
        owner = item.get("owner", {}).get("login", "")

        # 🔥 NOVO: construir URL manualmente (100% confiável)
        zip_url = f"https://api.github.com/repos/{owner}/{repo_name}/zipball"

        folder = os.path.join(base_folder, repo_name)

        print(f"⬇️ Baixando: {repo_name}")

        try:
            r = requests.get(zip_url)

            if r.status_code != 200:
                print(f"⚠️ Falha download: {repo_name}")
                continue

            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(folder)

            folders.append(folder)

        except Exception as e:
            print(f"⚠️ Erro ao extrair {repo_name}:", e)

    print("🎉 Download concluído!")

    return folders