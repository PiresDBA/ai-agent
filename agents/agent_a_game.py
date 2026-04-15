"""
Agent A — Game Developer
Especializado em criar jogos em Python/HTML5/Pygame.
Gera projetos funcionais e completos.
"""
import os
from core.llm import ask
from core.json_utils import extract_files_from_llm
from core.workspace import create_project_dir, write_files_to_project, save_project_manifest


def agent_a(task: str, model: str = None, mode: str = "fast") -> str:
    """
    Gera um projeto de jogo completo integrando com github_fetcher.

    Args:
        task: Descrição do jogo a criar

    Returns:
        Caminho da pasta do projeto gerado
    """
    print(f"🎮 [GAME AGENT] Criando jogo: {task[:60]}...")

    import shutil
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    try:
        from github_fetcher import github_fetch
        repos = github_fetch(task + " game")
        base_repo = repos[0] if repos else None
    except Exception as e:
        print("⚠️ Erro ao buscar Github:", e)
        base_repo = None

    repo_structure = ""
    if base_repo and os.path.exists(base_repo):
        try:
            items = os.listdir(base_repo)
            src = os.path.join(base_repo, items[0]) if len(items) == 1 and os.path.isdir(os.path.join(base_repo, items[0])) else base_repo
            files_list = []
            for root, _, files in os.walk(src):
                for file in files:
                    files_list.append(os.path.relpath(os.path.join(root, file), src))
            repo_structure = "\nESTRUTURA ATUAL DA BASE CLONADA DO GITHUB (VOCÊ DEVE INTEGRAR SEUS SCRIPTS COM ELA):\n" + "\n".join(f"- {f}" for f in files_list[:40]) + "\n"
        except Exception:
            pass

    prompt = f"""Você é o MELHOR DESENVOLVEDOR DE JOGOS DO MUNDO (Diamond Level).
FILOSOFIA OBRIGATÓRIA: NUNCA REMOVA SEM NECESSIDADE VITAL, SOMENTE MELHORE E CORRIJA, MELHORIA CONTINUA E EXCELENCIA!

Sua missão é criar uma OBRA DE ARTE em código: um jogo que seja o "DIAMANTE" máximo de qualidade.

TAREFA: {task}
{repo_structure}

PADRÕES PROFISSIONAIS (QUALIDADE DIAMANTE):
1. ARQUITETURA MODERNA: Use Classes, Design Patterns e separação clara de lógica e renderização.
2. ROBUSTEZ: Tratamento de exceções profissional. O jogo NUNCA deve crashar.
3. DOCUMENTAÇÃO PRÊMIUM: Use Docstrings (PEP 257) e Type Hinting rigoroso.
4. GAMEPLAY POLIDO: Transições suaves, sistema de pontuação persistente e dificuldade progressiva.
5. INTEGRAÇÃO GITHUB: Se houver base clonada, sua integração deve ser perfeita, elevando o projeto ao nível Diamond.

FORMATO DE SAÍDA:
```linguagem # nome_do_arquivo.ext
# Documentação Diamond
# Código Industrial Completo
```

Arquivos esperados: `main.py`, `requirements.txt`, `manual.md`."""

    response = ask("game_developer", prompt, model=model, timeout=180)

    if not response or len(response) < 100:
        # Fallback: jogo snake simples garantido funcionar
        return _fallback_snake_game(task)

    # Extrai arquivos da resposta do LLM
    files = extract_files_from_llm(response)

    if not files:
        # Tenta extrair apenas como código python
        files = {"main.py": _extract_first_code_block(response)}

    if not any(files.values()):
        return _fallback_snake_game(task)

    # Adiciona manual se não veio
    if "manual.md" not in files and "manual.md" not in {k.lower() for k in files}:
        files["manual.md"] = _generate_readme(task, files)

    # Salva na workspace
    project_path = create_project_dir(task)

    if base_repo and os.path.exists(base_repo):
        try:
            items = os.listdir(base_repo)
            src = os.path.join(base_repo, items[0]) if len(items) == 1 and os.path.isdir(os.path.join(base_repo, items[0])) else base_repo
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(project_path, item)
                if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                else: shutil.copy2(s, d)
        except Exception as e:
            print("⚠️ Erro ao mesclar repositório base:", e)

    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "A", created)

    print(f"  ✅ Projeto salvo em: {project_path}")
    print(f"  📁 Arquivos criados: {list(files.keys())}")

    return project_path


def _extract_first_code_block(text: str) -> str:
    """Extrai o primeiro bloco de código da resposta."""
    import re
    match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _generate_readme(task: str, files: dict) -> str:
    file_list = "\n".join(f"- {f}" for f in files.keys())
    return f"""# {task[:60]}

Projeto gerado automaticamente pelo Sistema de Agentes AI.

## Arquivos
{file_list}

## Como Executar

### Python:
```bash
pip install -r requirements.txt
python main.py
```

### Web (HTML5):
Abra `index.html` no navegador.

## Controles
- Setas ou WASD: Movimento
- Espaço: Ação principal
- ESC: Pausar/Sair
"""


def _fallback_snake_game(task: str) -> str:
    """Jogo snake garantidamente funcional como fallback."""
    snake_code = '''import pygame
import random
import sys

pygame.init()
WIDTH, HEIGHT = 600, 600
CELL = 20
FPS = 10

WHITE = (255,255,255)
BLACK = (20,20,20)
GREEN = (50,200,50)
RED = (220,50,50)
GRAY = (40,40,40)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 24)
big_font = pygame.font.SysFont("monospace", 48)

def draw_grid():
    for x in range(0, WIDTH, CELL):
        pygame.draw.line(screen, GRAY, (x,0), (x,HEIGHT))
    for y in range(0, HEIGHT, CELL):
        pygame.draw.line(screen, GRAY, (0,y), (WIDTH,y))

def game():
    snake = [(300,300),(280,300),(260,300)]
    direction = (CELL,0)
    food = (random.randrange(0,WIDTH,CELL), random.randrange(0,HEIGHT,CELL))
    score = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != (0,CELL): direction=(0,-CELL)
                if event.key == pygame.K_DOWN and direction != (0,-CELL): direction=(0,CELL)
                if event.key == pygame.K_LEFT and direction != (CELL,0): direction=(-CELL,0)
                if event.key == pygame.K_RIGHT and direction != (-CELL,0): direction=(CELL,0)
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        head = (snake[0][0]+direction[0], snake[0][1]+direction[1])

        if (head in snake or head[0]<0 or head[0]>=WIDTH or head[1]<0 or head[1]>=HEIGHT):
            screen.fill(BLACK)
            msg = big_font.render("GAME OVER", True, RED)
            sub = font.render(f"Score: {score} | R = Restart", True, WHITE)
            screen.blit(msg, (WIDTH//2-msg.get_width()//2, HEIGHT//2-60))
            screen.blit(sub, (WIDTH//2-sub.get_width()//2, HEIGHT//2+10))
            pygame.display.flip()
            waiting = True
            while waiting:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_r: return game()
                        if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            continue

        snake.insert(0, head)
        if head == food:
            score += 1
            food = (random.randrange(0,WIDTH,CELL), random.randrange(0,HEIGHT,CELL))
        else:
            snake.pop()

        screen.fill(BLACK)
        draw_grid()
        for i, seg in enumerate(snake):
            color = (50,220,50) if i==0 else GREEN
            pygame.draw.rect(screen, color, (*seg, CELL-2, CELL-2), border_radius=4)
        pygame.draw.rect(screen, RED, (*food, CELL-2, CELL-2), border_radius=4)
        score_txt = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_txt, (10,10))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    game()
'''
    project_path = create_project_dir(task)
    files = {
        "main.py": snake_code,
        "requirements.txt": "pygame>=2.0.0\n",
        "README.md": f"# Snake Game\n\n{task}\n\n## Executar\n```bash\npip install pygame\npython main.py\n```\n\n## Controles\n- Setas: mover\n- R: reiniciar\n- ESC: sair\n"
    }
    created = write_files_to_project(project_path, files)
    save_project_manifest(project_path, task, "A", created)
    return project_path