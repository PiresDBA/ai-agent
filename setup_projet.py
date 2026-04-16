import os

folders = [
    "agents",
    "core",
    "tools",
    "workspace",
    "knowledge"
]

files = {
    "agents/__init__.py": "",
    "core/__init__.py": "",
    "tools/__init__.py": "",
}

# criar pastas
for f in folders:
    os.makedirs(f, exist_ok=True)

# criar arquivos
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

print("✅ Estrutura criada com sucesso!")