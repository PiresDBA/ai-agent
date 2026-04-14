from playwright.sync_api import sync_playwright
import os

def clone(url):
    name = url.replace("https://", "").replace("http://", "").replace(".", "_")
    folder = f"workspace/clone_{name}"

    os.makedirs(folder, exist_ok=True)

    print(f"🌐 Clonando: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
        except:
            print("⚠️ Timeout, tentando continuar...")

        html = page.content()

        with open(f"{folder}/index.html", "w", encoding="utf-8") as f:
            f.write(html)

        browser.close()

    print(f"✅ Clone salvo em: {folder}")
    return folder


# 🔒 IMPORTANTE: só roda se executar direto
if __name__ == "__main__":
    url = input("🌍 URL: ")
    clone(url)