from engine.llm_guard import call_ollama

def ask(agent, prompt):
    return call_ollama(agent, prompt)