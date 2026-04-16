from playwright.sync_api import sync_playwright
import os
import requests
from urllib.parse import urlparse

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "cloned_site")
ASSETS_DIR = os.path.join(OUTPUT_DIR, "assets")

os.makedirs(ASSETS_DIR, exist_ok=True)

# =========================
# SALVAR ARQUIVOS
# =========================
def save_asset(url):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        filename = os.path.basename(urlparse(url).path)

        if not filename:
            return None

        path = os.path.join(ASSETS_DIR, filename)

        with open(path, "wb") as f:
            f.write(response.content)

        return filename

    except:
        return None

# =========================
# CLONAR SITE
# =========================
def clone_site(url):
    print("🌐 Clonando:", url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # armazenar assets capturados
        asset_map = {}

        def handle_response(response):
            try:
                req_url = response.url

                if any(ext in req_url for ext in [".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".gif"]):
                    filename = save_asset(req_url)
                    if filename:
                        asset_map[req_url] = f"assets/{filename}"

            except:
                pass

        page.on("response", handle_response)

        print("⏳ Carregando página...")
        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        page.wait_for_timeout(6000)

        html = page.content()

        browser.close()

    # =========================
    # REESCREVER LINKS
    # =========================
    for original, local in asset_map.items():
        html = html.replace(original, local)

    # =========================
    # SALVAR HTML
    # =========================
    index_path = os.path.join(OUTPUT_DIR, "index.html")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ Clone completo salvo!")

    print("📂 Caminho:", index_path)

    # =========================
    # ABRIR NO WINDOWS
    # =========================
    os.startfile(index_path)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    url = input("🌍 URL do site: ")
    clone_site(url)