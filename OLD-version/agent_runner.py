from crewai import Agent, Task, Crew

# =========================
# CONFIG LLM LOCAL (OLLAMA)
# =========================
llm = "ollama/deepseek-coder"

# =========================
# AGENTES
# =========================

dev_agent = Agent(
    role="Senior Python Developer",
    goal="Gerar código Python limpo e executável",
    backstory="Você escreve apenas código funcional, sem explicações.",
    llm=llm,
    verbose=True
)

test_agent = Agent(
    role="QA Engineer",
    goal="Garantir que o código não tenha erros",
    backstory="Você revisa código e remove qualquer coisa inválida.",
    llm=llm,
    verbose=True
)

# =========================
# TASK
# =========================

task = Task(
    description="""
Crie um jogo completo de Snake em Python usando pygame.

REGRAS:
- Retorne SOMENTE código Python
- NÃO escreva explicações
- NÃO use markdown ()

O código deve ser executável diretamente.
""",
    expected_output="Código Python completo e executável",
    agent=dev_agent
)

# =========================
# CREW
# =========================

crew = Crew(
    agents=[dev_agent, test_agent],
    tasks=[task],
    verbose=True
)

# =========================
# EXECUÇÃO
# =========================

result = crew.kickoff()

print("\n===== DEBUG RESULT =====\n")
print(result)

# =========================
# CAPTURA CORRETA DO OUTPUT
# =========================

try:
    output = result.raw
except:
    try:
        output = result.output
    except:
        output = str(result)

print("\n===== OUTPUT EXTRAÍDO =====\n")
print(output)

# =========================
# VALIDAÇÃO
# =========================

if not output or len(output.strip()) < 20:
    print("❌ ERRO: agente não retornou código válido")
    exit()

# =========================
# LIMPEZA SIMPLES
# =========================

if "" in output:
    parts = output.split("```")
    if len(parts) >= 2:
        output = parts[1]

# =========================
# SALVAR ARQUIVO
# =========================

file_name = "snake_game.py"

with open(file_name, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\n✅ Código salvo em {file_name}")