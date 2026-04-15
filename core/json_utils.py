"""
Utilitários robustos para parsing de JSON vindo de LLMs.
LLMs frequentemente adicionam markdown, texto extra, etc.
"""
import json
import re


def safe_json_load(text: str) -> dict:
    """
    Tenta extrair JSON válido de uma resposta LLM de forma tolerante.
    Lida com: blocos ```json, texto extra, chaves aninhadas mal formadas.
    """
    if not text:
        raise ValueError("Resposta LLM vazia")

    text = text.strip()

    # Remove blocos de código markdown
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "").strip()

    # Tenta JSON direto primeiro
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extrai primeiro bloco JSON válido
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Tenta extrair array JSON
    start_arr = text.find("[")
    end_arr = text.rfind("]")

    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        try:
            return json.loads(text[start_arr:end_arr + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Nenhum JSON válido encontrado na resposta: {text[:200]}")


def extract_code_blocks(text: str) -> list[dict]:
    """
    Extrai todos os blocos de código de uma resposta LLM.
    Retorna lista de {'lang': str, 'code': str, 'filename': str|None}
    """
    blocks = []

    # Padrão: ```lang\ncode\n```
    pattern = r"```(\w+)?\s*(?:#\s*(\S+)\s*)?\n(.*?)```"
    matches = re.finditer(pattern, text, re.DOTALL)

    for match in matches:
        lang = match.group(1) or "text"
        filename = match.group(2)
        code = match.group(3).strip()

        if code:
            blocks.append({
                "lang": lang,
                "code": code,
                "filename": filename
            })

    return blocks


def extract_files_from_llm(response: str) -> dict[str, str]:
    """
    Extrai múltiplos arquivos de uma resposta LLM de forma robusta.
    Prioriza o bloco mais longo para cada arquivo em caso de duplicatas.
    """
    files = {}

    def add_file(name, content):
        name = name.strip()
        content = content.strip()
        if not name or not content: return
        if name not in files or len(content) > len(files[name]):
            files[name] = content

    # Formato A: ```lang # filename.ext\ncode\n```
    pattern_lang_file = r"```(?:\w+)?[ \t]*#?[ \t]*([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)[ \t]*\n(.*?)```"
    for match in re.finditer(pattern_lang_file, response, re.DOTALL):
        add_file(match.group(1), match.group(2))

    # Formato B: ```python\n# main.py\ncode\n```
    pattern_generic = r"```(?:\w+)?[ \t]*\n(.*?)```"
    for match in re.finditer(pattern_generic, response, re.DOTALL):
        block_content = match.group(1).strip()
        lines = block_content.splitlines()
        if not lines: continue
        
        first_line = lines[0].strip()
        file_match = re.search(r"^(?:#|//|--|[/\*]*)\s*([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)\s*$", first_line)
        if file_match:
            add_file(file_match.group(1), "\n".join(lines[1:]))

    # Formato C: === filename ===
    pattern_sep = r"===\s*([^\n]+\.\w+)\s*===\s*\n(.*?)(?====|\Z)"
    for match in re.finditer(pattern_sep, response, re.DOTALL):
        add_file(match.group(1), match.group(2))

    # Formato D: # FILE: filename
    pattern_file_tag = r"#\s*FILE:\s*([^\n]+\.\w+)\s*\n(.*?)(?=#\s*FILE:|\Z)"
    for match in re.finditer(pattern_file_tag, response, re.DOTALL):
        add_file(match.group(1), match.group(2))

    # Fallback ext_map
    if not files:
        ext_map = {"python": "main.py", "javascript": "main.js", "html": "index.html", "css": "style.css"}
        pattern_fallback = r"```(python|javascript|html|css)[ \t]*\n(.*?)```"
        for match in re.finditer(pattern_fallback, response, re.DOTALL):
            add_file(ext_map.get(match.group(1), "unknown.txt"), match.group(2))

    return files