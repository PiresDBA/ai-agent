from core.llm import ask

def agent_a(task):
    return ask("game_agent", f"""
Você cria jogos AAA.

Use Unreal/Unity/Godot conforme necessário.

Crie estrutura para:
{task}

Inclua:
- gameplay loop
- input system
- rendering setup
""")