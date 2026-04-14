from crewai import Agent, Task, Crew
import subprocess
import time

# =========================
# CONFIG LLM LOCAL (OLLAMA)
# =========================
llm = "ollama/gemma4:e4b"

# =========================
# AGENTES
# =========================

dev_agent = Agent(
    role="Senior Python Game Developer",
    goal="Gerar código Python limpo e executável",
    backstory="Você escreve apenas código Python funcional, sem explicações.",
    llm=llm,
    verbose=True
)

fix_agent = Agent(
    role="Senior Python Debugger",
    goal="Corrigir erros em código Python",
    backstory="Especialista em corrigir bugs e retornar código limpo",
    llm=llm,
    verbose=True
)

# =========================
# TASK INICIAL
# =========================

task = Task(
    description="""
You must generate ONLY valid Python code.

Create a Snake game using pygame.

STRICT RULES:
- Output ONLY Python code
- DO NOT include explanations
- DO NOT include comments
- DO NOT include markdown
- DO NOT include HTML or links

The code must:
- be complete
- be executable
- start with imports
- have no syntax errors
""",
    expected_output="Pure Python code",
    agent=dev_agent
)

# =========================
# CREW INICIAL
# =========================

crew = Crew(
    agents=[dev_agent],
    tasks=[task],
    verbose=True
)

# =========================
# FUNÇÃO: EXECUTAR CÓDIGO
# =========================

def run_code(file_name):
    try:
        result = subprocess.run(
            ["python", file_name],
            capture_output=True,
            text=True,
            timeout=20
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

# =========================
# FUNÇÃO: CORRIGIR CÓDIGO
# =========================

def fix_code(code, error):
    fix_task = Task(
        description=f"""
Fix this Python code.

ERROR:
{error}

CODE:
{code}

RULES:
- Return ONLY corrected Python code
- Do NOT explain anything
- Do NOT add text
""",
        expected_output="Corrected Python code",
        agent=fix_agent
    )

    fix_crew = Crew(
        agents=[fix_agent],
        tasks=[fix_task],
        verbose=True
    )

    result = fix_crew.kickoff()

    try:
        return result.raw
    except:
        return str(result)

# =========================
# FUNÇÃO: EXTRAIR OUTPUT
# =========================

def extract_output(result):
    try:
        output = result.raw
    except:
        try:
            output = result.output
        except:
            output = str(result)

    if "```" in output:
        parts = output.split("```")
        if len(parts) >= 2:
            output = parts[1]

    return output

# =========================
# EXECUÇÃO PRINCIPAL
# =========================

print("\n🚀 Gerando código inicial...\n")

result = crew.kickoff()
output = extract_output(result)

# valida saída
if not output or len(output.strip()) < 20:
    print("❌ ERRO: modelo não retornou código válido")
    exit()

file_name = "snake_game.py"

# salva primeira versão
with open(file_name, "w", encoding="utf-8") as f:
    f.write(output)

print("✅ Código inicial salvo!")

# =========================
# LOOP DE CORREÇÃO AUTOMÁTICA
# =========================

max_attempts = 5

for attempt in range(max_attempts):
    print(f"\n🔁 Tentativa {attempt + 1} de execução...\n")

    stdout, stderr = run_code(file_name)

    if not stderr:
        print("🎉 Código executou com sucesso!")
        print(stdout)
        break

    print("❌ ERRO DETECTADO:\n", stderr)

    with open(file_name, "r", encoding="utf-8") as f:
        code = f.read()

    print("\n🧠 Corrigindo com IA...\n")

    fixed_code = fix_code(code, stderr)

    if not fixed_code or len(fixed_code.strip()) < 20:
        print("❌ Falha ao corrigir código")
        break

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(fixed_code)

    print("✅ Código corrigido! Tentando novamente...\n")

    time.sleep(2)

else:
    print("\n⚠️ Não foi possível corrigir após várias tentativas.")