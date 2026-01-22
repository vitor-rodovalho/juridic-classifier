from enum import Enum
from pydantic import BaseModel, Field




class CategoryEnum(str, Enum):
    PROCESSUAL = "Processual"
    FINANCEIRO = "Financeiro"
    SUPORTE = "Suporte Técnico"
    COMERCIAL = "Comercial"
    ADMINISTRATIVO = "Administrativo"
    OUTROS = "Outros"



class ClassificationRequest(BaseModel):
    text: str = Field(
        ..., 
        min_length=3, 
        max_length=2000, 
        description="Texto da mensagem enviada pelo usuário.",
        example="Gostaria de agendar uma sala para fazer uma reunião."
    )



class ClassificationResponse(BaseModel):
    category: CategoryEnum = Field(..., description="Categoria classificada.")
    reasoning: str = Field(..., description="Explicação do motivo da classificação.")
    model: str = Field(..., description="Modelo utilizado (ex: Llama3 ou Heuristic).")
    strategy: str = Field(..., description="Estratégia utilizada: 'LLM' ou 'Fallback-Heuristic'.")