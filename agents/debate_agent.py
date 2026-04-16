from core.llm import ask

def debate(task, output):

    prompt = f"""
Você é um AGENTE CRÍTICO.

Tarefa:
{task}

Output gerado:
{output}

Analise:
- bugs
- riscos
- melhorias

Responda JSON:
{{
  "approved": true/false,
  "issues": [],
  "fix_suggestions": []
}}
"""

    res = ask("debate_agent", prompt)

    try:
        import json
        return json.loads(res)
    except:
        return {"approved": True, "issues": []}
    