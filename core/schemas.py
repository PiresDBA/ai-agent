from pydantic import BaseModel, Field
from typing import Literal


class RouteDecision(BaseModel):
    route: Literal["A", "B", "C"]
    confidence: float = Field(ge=0.0, le=1.0)