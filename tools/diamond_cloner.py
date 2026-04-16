"""
Diamond Cloner — Utilitário de alto nível para clonagem e rebranding de sites.
Inspirado no Site_cloner_2.0.py pessoal do usuário.
"""
import os
import re
import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright

WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace")

class DiamondCloner:
    def __init__(self, target_url, project_name):
        self.target_url = target_url
        self.project_name = project_name
        self.parsed = urlparse(target_url)
        self.base_domain = self.parsed.netloc
        self.visited = set()
        self.url_map = {}
        
        # Pasta do projeto
        safe_name = re.sub(r'\W+', '_', project_name.lower())
        self.project_dir = os.path.join(WORKSPACE, f"clone_{safe_name}")
        os.makedirs(self.project_dir, exist_ok=True)

    def _clean_name(self, url):
        path = url.replace("https://", "").replace("http://", "")
        path = path.replace(self.base_domain, "")
        path = re.sub(r'\W+', '_', path)
        if not path or path == "_":
            return "index"
        return path.strip("_")

    def _rebrand(self, html):
        """Aplica rebranding Diamond substituindo termos do site original."""
        patterns = [
            self.base_domain.split('.')[0], # ex: 'webmotors'
            "Webmotors", "OLX", "Mercado Livre", "MercadoLivre"
        ]
        
        rebranded = html
        for p in patterns:
            # Substituição case-insensitive mantendo o padrão se possível (limitado)
            rebranded = re.sub(p, self.project_name, rebranded, flags=re.IGNORECASE)
            
        # Troca títulos
        rebranded = re.sub(r'<title>.*?</title>', f'<title>💎 {self.project_name}</title>', rebranded, flags=re.IGNORECASE)
        
        return rebranded

    async def save_page(self, page, url):
        name = self._clean_name(url)
        file_name = f"{name}.html"
        self.url_map[url] = file_name
        
        print(f"  💾 Clonando página: {url} -> {file_name}")
        
        content = await page.content()
        rebranded_content = self._rebrand(content)
        
        path = os.path.join(self.project_dir, file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(rebranded_content)

    async def rewrite_links(self):
        print("  🔁 Corrigindo links internos Diamond...")
        for file in os.listdir(self.project_dir):
            if not file.endswith(".html"):
                continue
            
            path = os.path.join(self.project_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            
            for original, local in self.url_map.items():
                html = html.replace(original, local)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

    async def crawl(self, page, url, depth=0):
        if depth > 1 or url in self.visited: # Limite Diamond 1 pra ser rápido (apenas as principais)
            return
        
        self.visited.add(url)
        
        try:
            print(f"  🔎 Navegando: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000) # Deixa JS respirar
            
            await self.save_page(page, url)
            
            # Extrai links do mesmo domínio
            links = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            valid_links = [l for l in links if self.base_domain in l and l not in self.visited]
            
            for link in valid_links[:3]: # Limite de links por nível
                await self.crawl(page, link, depth + 1)
        except Exception as e:
            print(f"  ⚠️ Erro ao clonar {url}: {e}")

    async def run(self):
        async with async_playwright() as p:
            print(f"🚀 Iniciando Diamond Cloner para: {self.target_url}")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()
            
            await self.crawl(page, self.target_url)
            
            await browser.close()
        
        await self.rewrite_links()
        return self.project_dir

def clone_site_diamond(url, name):
    """Entrypoint síncrono para integração com pipeline existente."""
    cloner = DiamondCloner(url, name)
    return asyncio.run(cloner.run())
