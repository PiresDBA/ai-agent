"""
Diamond Crew Factory — Orquestração de Agentes CrewAI.
Otimizado para rodar localmente com 2 agentes (Lead + Developer).
"""
import os
from crewai import Agent, Task, Crew, Process
from core.llm import get_crewai_llm

# Configura o endpoint do Ollama para o LiteLLM interno do CrewAI
os.environ["OLLAMA_API_BASE"] = "http://127.0.0.1:11434"
# Diamond Stability: Aumenta o timeout global do LiteLLM (em segundos)
os.environ["LITELLM_REQUEST_TIMEOUT"] = "600"
os.environ["LITELLM_RETRY_DELAY"] = "2"
os.environ["LITELLM_NUM_RETRIES"] = "3"

class DiamondCrew:
    @staticmethod
    def create_technical_crew(task_description: str, model_name: str = None):
        """Cria um time de elite com 2 agentes para resolver tarefas complexas."""
        llm = get_crewai_llm(model_name)

        # 1. Agente Arquiteto (Líder Técnico)
        architect = Agent(
            role='Technical Architect',
            goal=f'Plan and design the elite solution for: {task_description}',
            backstory='You are a Diamond-level Tech Lead. You focus on architecture, structure, and quality standards.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        # 2. Agente Desenvolvedor (Executor)
        developer = Agent(
            role='Senior Developer',
            goal=f'Implement the full logic and tests for: {task_description}',
            backstory='You are a world-class coder. You write Clean Code, robust logic, and mandatory test suites.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        # Tarefas
        t1 = Task(
            description=f'Design the project structure and technical requirements for: {task_description}. Ensure Diamond standards.',
            agent=architect,
            expected_output='A detailed technical plan including folder structure and main logic flow.'
        )

        t2 = Task(
            description=f'Based on the plan, implement the final Python code and a Pytest suite. NEVER use placeholders.',
            agent=developer,
            expected_output='The final functional code and test suite.',
            context=[t1]
        )

        # Orquestração
        return Crew(
            agents=[architect, developer],
            tasks=[t1, t2],
            process=Process.sequential,
            verbose=True
        )

def run_diamond_crew(task_description: str, model_name: str = None) -> str:
    """Executa a crew e retorna a resposta final concatenada."""
    crew = DiamondCrew.create_technical_crew(task_description, model_name)
    result = crew.kickoff()
    return str(result)
