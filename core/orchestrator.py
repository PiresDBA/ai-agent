"""
Orquestrador Inteligente v5 — O Cérebro do Sistema.
Identidade: Você pensa, decide, delega e garante que o trabalho seja feito pelo agente certo.

PROTOCOLOS OBRIGATÓRIOS:
1. ENTENDER: Identificar intenção real vs literal.
2. CLASSIFICAR: Mapear para Games, App, Automation ou Chat.
3. PLANEJAR: Definir ordem e critérios de sucesso.
4. CONTEXTUALIZAR: Delegar com histórico e objetivos completos.
5. CONSOLIDAR: Unificar resultados em uma saída coesa.
"""
import json
import os
from difflib import SequenceMatcher
from functools import lru_cache

from core.llm import ask
from core.schemas import RouteDecision
from core.json_utils import safe_json_load
from core.memory import get_best_route_hint

# ===================================================
# KNOWLEDGE BASE — keywords por categoria de agente
# ===================================================
ROUTES_KB = {
    "A": [
        "game", "jogo", "jogos", "unity", "unreal", "godot", "fps", "arcade",
        "platformer", "rpg", "puzzle", "snake", "tetris", "pong", "simulador",
        "shooter", "aventura", "2d", "3d", "sprite", "pixel art"
    ],
    "B": [
        "imposto", "tax", "financeiro", "saas", "dashboard", "api", "web app",
        "contabilidade", "relatorio", "crud", "banco de dados", "backend",
        "frontend", "site", "aplicação web", "sistema", "gestao", "painel",
        "e-commerce", "loja", "cadastro", "login", "autenticação"
    ],
    "C": [
        "git", "clone", "script", "automation", "automação", "refactor",
        "tooling", "cli", "bot", "crawler", "scraper", "etl", "pipeline",
        "processamento", "conversão", "arquivo", "pdf", "excel", "csv"
    ],
    "D": [
        "quem é", "paises", "população", "ações", "notícias", "chat", "oi", "bom dia",
        "boa tarde", "boa noite", "ajuda", "clima", "tempo", "diferença", "explicar",
        "resumo", "conversa", "olá", "tudo bem", "stats", "estatística", "conversar",
        "falaremos", "falar", "responda", "me diga", "quem", "quanto", "lista",
        "amigo", "conhece", "você", "entende", "sabe", "bom dia", "boa tarde",
        "neymar", "messi", "cristiano", "futebol", "esporte", "biografia", "fama",
        "história", "curiosidades", "pergunta", "fale sobre", "explica", "quem foi"
    ]
}


# ===================================================
# MEMÓRIA DE APRENDIZADO LOCAL (router_memory.json)
# ===================================================
_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "router_memory.json")
_router_memory: dict = {}


def _load_router_memory() -> dict:
    global _router_memory
    if os.path.exists(_MEMORY_FILE):
        try:
            with open(_MEMORY_FILE, "r", encoding="utf-8") as f:
                _router_memory = json.load(f)
        except Exception:
            _router_memory = {}
    return _router_memory


def _save_router_memory():
    try:
        with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_router_memory, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# Inicializa ao importar
_load_router_memory()


def _memory_router(text: str) -> tuple[str | None, float]:
    """Verifica se já roteamos esta tarefa idêntica antes."""
    key = text.lower().strip()[:200]  # normaliza e limita tamanho da chave
    if key in _router_memory:
        entry = _router_memory[key]
        return entry["route"], 0.99
    return None, 0.0


def _learn(text: str, route: str):
    """Registra uma decisão de roteamento para aprendizado futuro."""
    key = text.lower().strip()[:200]
    _router_memory[key] = {"route": route, "count": _router_memory.get(key, {}).get("count", 0) + 1}
    # Limite de 1000 entradas (evita crescimento infinito)
    if len(_router_memory) > 1000:
        oldest = list(_router_memory.keys())[0]
        del _router_memory[oldest]
    _save_router_memory()


# ===================================================
# REGRAS EXPLÍCITAS (alta precisão, sem LLM)
# ===================================================
def _rule_router(text: str) -> tuple[str | None, float]:
    t = text.lower()
    for route, keywords in ROUTES_KB.items():
        for kw in keywords:
            if kw in t:
                return route, 1.0
    return None, 0.0


# ===================================================
# SIMILARLY SEMÂNTICA (SequenceMatcher)
# ===================================================
def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _semantic_score(text: str, keywords: list[str]) -> float:
    return max(_similarity(text, k) for k in keywords)


def _semantic_router(text: str) -> tuple[str, float]:
    scores = {
        route: _semantic_score(text, keywords)
        for route, keywords in ROUTES_KB.items()
    }
    best = max(scores, key=scores.get)
    return best, scores[best]


# ===================================================
# LLM ROUTER — árbitro final
# ===================================================
def _llm_router(text: str) -> tuple[str | None, float]:
    prompt = f"""IDENTIDADE:
Você é o Orquestrador, o agente central e mais importante do sistema.
Você não executa tarefas diretamente. Você pensa, decide, delega e garante que o trabalho seja feito pelo agente certo.

AGENTES SOB SEU COMANDO:
→ GAMES AGENT: Jogos, mecânicas, física de jogo, NPCs.
→ APP AGENT: Telas, UI/UX, fluxos de usuário, mobile/web features.
→ AUTOMATION AGENT: Scripts, bots, pipelines, integrações, webhooks.
→ CHAT AGENT (BULLDOG FRIDA): Conversas, dúvidas, triagem, explicações.

PROTOCOLO DE DECISÃO:
1. ENTENDER: O que o usuário realmente quer?
2. CLASSIFICAR: Identifique o agente (A, B, C ou D).
3. PLANEJAR: Monte a ordem se houver múltiplas tarefas.

PROTOCOLO DE AMBIGUIDADE:
Se for vago, NÃO escolha. Peça esclarecimento: "Para eu direcionar isso corretamente, preciso entender: [UMA pergunta específica]".

TAREFA DO USUÁRIO: {text}

Responda SOMENTE com JSON válido:
{{
  "route": "A/B/C/D", 
  "confidence": 0.99, 
  "reason": "motivo", 
  "is_ambiguous": false,
  "clarification_question": ""
}}"""

    raw = ask("router", prompt, timeout=30)

    try:
        data = safe_json_load(raw)
        route = data.get("route", "").upper()
        conf = float(data.get("confidence", 0))
        if route in ("A", "B", "C", "D"):
            return route, conf
    except Exception:
        pass

    return None, 0.0


# ===================================================
# SMART ROUTE — pipeline completo de decisão
# ===================================================
def smart_route(text: str) -> RouteDecision:
    # 1. Memória de aprendizado amplo (task memory)
    hint = get_best_route_hint(text)
    if hint and hint in ("A", "B", "C", "D"):
        return RouteDecision(route=hint, confidence=0.99, reason="task_memory")

    # 2. Memória local do router
    mem_route, mem_score = _memory_router(text)
    if mem_route:
        return RouteDecision(route=mem_route, confidence=mem_score, reason="router_memory")

    # 3. Regras explícitas (mais rápido, sem LLM)
    rule_route, rule_score = _rule_router(text)
    if rule_route:
        _learn(text, rule_route)
        return RouteDecision(route=rule_route, confidence=rule_score, reason="rule_match")

    # 4. Similaridade semântica
    sem_route, sem_score = _semantic_router(text)
    if sem_score > 0.75:
        _learn(text, sem_route)
        return RouteDecision(route=sem_route, confidence=sem_score, reason="semantic_match")

    # 5. LLM como árbitro final
    llm_route, llm_conf = _llm_router(text)
    if llm_route and llm_conf > 0.5:
        _learn(text, llm_route)
        return RouteDecision(route=llm_route, confidence=llm_conf, reason="llm_decision")

    # 6. Fallback seguro
    return RouteDecision(route="C", confidence=0.3, reason="fallback_safe")


@lru_cache(maxsize=256)
def _cached_route(text: str) -> RouteDecision:
    return smart_route(text)


def route(text: str, use_cache: bool = True, forced_route: str = None) -> RouteDecision:
    """Entrypoint principal do orquestrador."""
    # 0. Manual Override (Gold Rule: User Choice First)
    if forced_route and forced_route in ("A", "B", "C", "D"):
        return RouteDecision(route=forced_route, confidence=1.0, reason="manual_override")

    if use_cache:
        return _cached_route(text)
    return smart_route(text)