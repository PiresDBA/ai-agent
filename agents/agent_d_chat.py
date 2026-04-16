"""
CHAT AGENT (BULLDOG FRIDA): Conversas, dúvidas, triagem, explicações.
"""
from core.llm import ask

def agent_d(task: str, model: str = None, mode: str = "fast", history: list = None) -> str:
    """
    Responde a perguntas e solicitações de chat sem gerar projetos.
    Usa histórico para manter o contexto da conversa.
    """
    print(f"💬 [CHAT AGENT] Processando conversa: {task[:60]}...")
    
    # Reconstrói histórico para o prompt
    history_str = ""
    if history and len(history) > 0:
        for msg in history[-5:]: # Pega as últimas 5 trocas
            role = "USUÁRIO" if msg.get("role") == "user" else "FRIDA"
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"

    # Regra de Apresentação: Só se for o início da conversa (histórico vazio ou apenas a msg atual)
    saudacao_rule = ""
    if not history or len(history) <= 1:
        saudacao_rule = "<div class=\"avatar-ai\"></div>\nComece se apresentando: 'Olá, eu sou a Bulldogue Frida'."
    else:
        saudacao_rule = "NÃO se apresente, vá direto ao assunto, pois vocês já estão conversando."

    prompt = f"""IDENTIDADE:
Você é a Bulldogue Frida, especialista de elite em comunicação e atendimento.
Sua função é manter conversas contextuais, entender intenções e responder perguntas.

HISTÓRICO DA CONVERSA:
{history_str}
USUÁRIO: {task}

REGRAS:
- Seja direta, profissional e empática.
- {saudacao_rule}
- Responda apenas o que foi solicitado.
- Siga as regras de Bulldogue Elite: nada de placeholders, apenas excelência."""

    # Utiliza um timeout menor para respostas rápidas (Fast-Path)
    response = ask("bulldog_frida", prompt, model=model, timeout=120)
    
    if not response:
        return "⚠️  Desculpe, não consegui processar sua solicitação no momento. Por favor, tente novamente."
        
    return response
