"""
Schemas Pydantic — contratos de dados do sistema.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class RouteDecision(BaseModel):
    """Decisão do orquestrador sobre para qual agente rotear."""
    route: Literal["A", "B", "C"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class TaskResult(BaseModel):
    """Resultado padronizado de qualquer tarefa executada."""
    status: Literal["success", "partial", "failed"]
    route: str
    project_path: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    iterations: int = 0
    score: float = 0.0
    history: list = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    """Relatório de qualidade gerado pelo LLM."""
    score: float = Field(ge=0.0, le=1.0, default=0.5)
    issues: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class SecurityReport(BaseModel):
    """Relatório de segurança gerado pelo LLM."""
    approved: bool = True
    issues: list[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=1.0, default=0.0)