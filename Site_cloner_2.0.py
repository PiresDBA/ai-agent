from playwright.sync_api import sync_playwright
import os
import re
from urllib.parse import urlparse

# =========================
# CONFIG BASE
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

visited = set()
url_map = {}

# =========================
# LIMPAR NOME DE ARQUIVO
# =========================
def clean_name(url, base):
    path = url.replace("https://", "").replace("http://", "")
    path = path.replace(base, "")
    path = re.sub(r'\W+', '_', path)

    if not path or path == "_":
        return "index"

    return path.strip("_")

# =========================
# REBRANDING FORTE
# =========================
def rebrand(html, new_name):
    patterns = [
        r'Webmotors',
        r'WEBMOTORS',
        r'Web Motors',
        r'webmotors'
    ]

    for p in patterns:
        html = re.sub(p, new_name, html, flags=re.IGNORECASE)

    # troca título
    html = re.sub(r'<title>.*?</title>', f'<title>{new_name}</title>', html, flags=re.IGNORECASE)

    return html

# =========================
# EXTRAIR LINKS
# =========================
def get_links(page, base):
    links = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => e.href)"
    )

    valid = []

    for link in links:
        if base in link and link not in visited:
            valid.append(link)

    return valid

# =========================
# SALVAR HTML
# =========================
def save_page(page, url, base, project_dir, new_name):
    name = clean_name(url, base)
    file_name = f"{name}.html"

    html = page.content()
    html = rebrand(html, new_name)

    # salvar mapeamento
    url_map[url] = file_name

    path = os.path.join(project_dir, file_name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"💾 {file_name}")

# =========================
# REESCREVER LINKS INTERNOS
# =========================
def rewrite_links(project_dir):
    for file in os.listdir(project_dir):
        if not file.endswith(".html"):
            continue

        path = os.path.join(project_dir, file)

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        for original, local in url_map.items():
            html = html.replace(original, local)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    print("🔁 Links internos corrigidos!")

# =========================
# CRAWLER
# =========================
def crawl(page, url, base, project_dir, new_name, depth=0):
    if depth > 2:
        return

    if url in visited:
        return

    visited.add(url)

    print("🔎", url)

    page.goto(url, wait_until="domcontentloaded", timeout=60000)

# 🔥 espera conteúdo real aparecer
    try:
        page.wait_for_selector("body", timeout=10000)
    except:
        pass

# espera mais um pouco para JS montar
    page.wait_for_timeout(5000)


    save_page(page, url, base, project_dir, new_name)

    links = get_links(page, base)

    for link in links[:5]:
        crawl(page, link, base, project_dir, new_name, depth + 1)

# =========================
# MAIN
# =========================
url = input("🌍 URL: ")
new_name = input("🏷️ Novo nome do site: ")

parsed = urlparse(url)
base = parsed.netloc

# 🔥 criar pasta com nome do projeto
project_name = re.sub(r'\W+', '_', new_name.lower())
project_dir = os.path.join(BASE_DIR, f"clone_{project_name}")

os.makedirs(project_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        user_agent="Mozilla/5.0"
    )

    page = context.new_page()

    crawl(page, url, base, project_dir, new_name)

    browser.close()

# 🔥 corrigir links depois
rewrite_links(project_dir)

print("✅ Clone finalizado!")
print("📁 Pasta:", project_dir)

os.startfile(project_dir)