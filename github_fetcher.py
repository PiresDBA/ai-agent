import requests
import zipfile
import io
import os

GITHUB_API = "https://api.github.com/search/repositories"

def search_github(query, max_repos=3):
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos
    }

    response = requests.get(GITHUB_API, params=params)
    data = response.json()

    repos = []

    for item in data.get("items", []):
        repos.append({
            "name": item["name"],
            "full_name": item["full_name"],
            "zip_url": item["archive_url"].replace("{archive_format}{/ref}", "zipball"),
        })

    return repos


def download_and_extract(repo, base_folder):
    repo_name = repo["full_name"].replace("/", "_")
    folder_path = os.path.join(base_folder, repo_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    print(f"📥 Baixando {repo['full_name']}...")

    response = requests.get(repo["zip_url"])

    z = zipfile.ZipFile(io.BytesIO(response.content))
    z.extractall(folder_path)

    print(f"✅ Extraído em {folder_path}")


def github_fetch(query):
    base_folder = os.path.join("github_projects", query.replace(" ", "_"))

    if not os.path.exists(base_folder):
        os.makedirs(base_folder)

    repos = search_github(query)

    for repo in repos:
        download_and_extract(repo, base_folder)

    print("\n🎉 Download concluído!")


# =====================
# EXECUÇÃO
# =====================

if __name__ == "__main__":
    query = input("🔎 O que você quer buscar no GitHub? ")
    github_fetch(query)