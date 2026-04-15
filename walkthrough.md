# 🤖 Antigravity Agent System — Refatoração Completa

## O que foi feito

Reescrita completa de **12 arquivos** corrigindo **18 bugs críticos** e transformando o sistema num SaaS robusto.

## Bugs Corrigidos

| # | Arquivo | Bug | Status |
|---|---------|-----|--------|
| 1 | `pipeline.py` | Deadlock lógico: `stuck escape` após `return` (código morto) | ✅ |
| 2 | `pipeline.py` | `run_project()` recebia texto do LLM em vez de caminho de pasta | ✅ |
| 3 | `pipeline.py` | `pipeline_lock` global bloqueava a API inteira | ✅ |
| 4 | `quality.py` | Função `quality_check` duplicada — 2ª versão sobrescrevia a 1ª | ✅ |
| 5 | `security.py` | Retornava chave `safe`, pipeline verificava `approved` (nunca passava) | ✅ |
| 6 | `schemas.py` | Campo `reason` ausente no Pydantic → `ValidationError` | ✅ |
| 7 | `llm_scheduler.py` | Polling busy-wait sem timeout → loop infinito | ✅ |
| 8 | `agent_a/b/c.py` | Agentes retornavam texto, não caminhos de projeto | ✅ |
| 9 | `executor.py` | `exec()` inseguro sem captura de stdout/stderr | ✅ |
| 10 | `fixer.py` | Escrevia resposta LLM inteira em todos os `.py` | ✅ |
| 11 | `github_fetcher.py` | `requests` importado 2x, sem timeout nos downloads | ✅ |
| 12 | `git_manager.py` | `subprocess` importado 2x | ✅ |
| 13 | `pipeline.py` | FIXER_MODELS com nomes de modelos inexistentes | ✅ |
| 14 | `json_utils.py` | Sem extração de múltiplos arquivos do LLM | ✅ |
| 15 | `llm.py` | Sem detecção automática de modelos via API | ✅ |
| 16 | Geral | Sem sistema de workspace (projetos gerados perdidos) | ✅ |
| 17 | Geral | Sem encoding UTF-8 para terminal Windows | ✅ |
| 18 | Geral | Sem endpoint de health/status/projetos | ✅ |

## Melhorias de Arquitetura

### Core
- **`llm.py`** — Detecção automática de modelos via API Ollama, lock de GPU único, temperatura configurada, fallback inteligente 
- **`orchestrator.py`** — Keywords expandidas (30+), pipeline de 5 camadas de roteamento
- **`memory.py`** — Tracking de falhas + estatísticas (taxa de sucesso, score médio)
- **`workspace.py`** — Novo módulo: projetos isolados por tarefa com manifesto JSON
- **`json_utils.py`** — Extração de múltiplos arquivos de respostas LLM (formatos variados)

### Engine
- **`pipeline.py`** — AGI v9: sem locks globais, stuck-escape funcional, fallback de fallback
- **`executor.py`** — Subprocess seguro com captura de stdout/stderr e timeout
- **`quality.py`** — Avaliação via LLM + fallback heurístico
- **`security.py`** — Análise estática instantânea + LLM para código grande

### Agents
- **`agent_a`** — Gera projetos reais em `workspace/`, fallback snake game garantido
- **`agent_b`** — Gera apps FastAPI reais, fallback todo app completo
- **`agent_c`** — Gera scripts reais com README e requirements

### API
- **`api/main.py`** — FastAPI completo com:
  - `POST /run` — execução síncrona
  - `POST /run/async` — execução assíncrona com background tasks
  - `WebSocket /ws/{id}` — streaming de logs em tempo real
  - `GET /projects` — lista todos projetos
  - `GET /health` — status do Ollama
  - `GET /stats` — métricas de uso
  - Dashboard web embutido com exemplos de prompts

## Como Usar

### Iniciar
```bash
# 1. Garantir que Ollama está rodando
ollama serve

# 2. Instalar modelo (se ainda não tiver)
ollama pull llama3.2:3b

# 3. Iniciar o sistema
$env:PYTHONIOENCODING="utf-8"; python start.py
```

### Dashboard
Abra **http://localhost:8080** — use os botões de exemplo ou escreva seu prompt.

### API
```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Crie um jogo snake em Python"}'
```

## Verificação de Status

```
GET /health → {"status": "healthy", "ollama_online": true, "models": [...]}
```

Os 8 modelos detectados automaticamente:
- llama3.2:3b, gemma3:4b, deepseek-coder:latest
- qwen2.5-coder:7b, llama3.1:8b, mistral:latest
- codellama:latest, phi3:latest
