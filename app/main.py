import sys
import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from schemas import ClassificationRequest, ClassificationResponse
from classifier import Classifier


logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API de Classificação Jurídica Inteligente. Classifica mensagens em categorias específicas usando IA ou heurísticas.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Permite todas as origens, útil para testes mas deve ser restrito em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Inicializa o classificador
classifier = Classifier()




@app.middleware("http")
async def add_process_time_header(request: Request, call_next) -> JSONResponse:
    """Middleware para medir performance e logar requisições.
    
    Args:
        request: Objeto da requisição HTTP.
        call_next: Função para processar a requisição.
    
    Returns:
        JSONResponse: Resposta HTTP com header de tempo de processamento.
    """

    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    
    logger.info(f"HTTP request | method={request.method} | path={request.url.path} | status_code={response.status_code} | duration={round(process_time, 4)}s")
    
    return response




@app.get("/", tags=["Status"], responses={
    200: {
        "description": "API está online e funcionando",
        "content": {
            "application/json": {
                "example": {
                    "message": "Nexus Legal Classifier Online",
                    "docs": "/docs",
                    "version": "1.0.0"
                }
            }
        }
    }
})
async def root() -> dict:
    """
    Endpoint raiz que retorna informações sobre o status da API.
    
    Returns:
        dict: Dicionário com mensagem de status, documentação e versão.
    """
    logger.debug("Root endpoint accessed")
    
    return {
        "message": "Nexus Legal Classifier Online",
        "docs": "/docs",
        "version": settings.VERSION
    }




@app.get("/health", tags=["Status"], responses={
    200: {
        "description": "API está saudável e pronta para processar requisições",
        "content": {
            "application/json": {
                "example": {
                    "status": "healthy",
                    "mode": "LLM",
                    "model": "llama-3.3-70b-versatile"
                }
            }
        }
    }
})
async def health_check() -> dict:
    """
    Verifica o status de saúde da API e modo operacional.
    
    **Respostas:**
    - **200**: API está saudável
    
    **Modos de operação:**
    - `LLM`: API do Groq disponível (classificação com IA)
    - `Fallback`: Usando heurística local (sem acesso à API)
    
    Returns:
        dict: Status da saúde, modo (LLM ou Fallback) e modelo utilizado.
    """

    mode = "LLM" if settings.GROQ_API_KEY else "Fallback"
    logger.info(f"Health check | mode={mode} | model={settings.GROQ_MODEL}")

    return {
        "status": "healthy",
        "mode": mode,
        "model": settings.GROQ_MODEL
    }




@app.post("/classify", response_model=ClassificationResponse, tags=["Inference"], responses={
    200: {
        "description": "Classificação realizada com sucesso",
        "content": {
            "application/json": {
                "example": {
                    "category": "Processual",
                    "reasoning": "Questão sobre prazo e recurso processual",
                    "model": "llama-3.3-70b-versatile",
                    "strategy": "LLM (Groq)"
                }
            }
        }
    },
    400: {
        "description": "Texto vazio ou inválido",
        "content": {
            "application/json": {
                "example": {
                    "detail": "O texto da mensagem não pode estar vazio."
                }
            }
        }
    },
    422: {
        "description": "Validação de entrada falhou",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "text"],
                            "msg": "ensure this value has at least 3 characters",
                            "type": "value_error.string.too_short"
                        }
                    ]
                }
            }
        }
    },
    500: {
        "description": "Erro interno no servidor",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Erro interno no servidor de classificação."
                }
            }
        }
    }
})
async def classify_text(request: ClassificationRequest) -> ClassificationResponse:
    """
    Classifica um texto jurídico em categorias predefinidas.
    
    Utiliza IA (Groq LLM) quando disponível, com fallback para heurística baseada em palavras-chave.
    
    **Categorias disponíveis:**
    - `Processual`: Processos judiciais, prazos, audiências, recursos
    - `Financeiro`: Pagamentos, custas, honorários, cobranças
    - `Suporte Técnico`: Problemas técnicos, acesso, erros de sistema
    - `Comercial`: Novos negócios, propostas, parcerias
    - `Administrativo`: Agendamentos, documentos, logística
    - `Outros`: Saudações ou fora de contexto
    
    **Estratégias utilizadas:**
    - `LLM (Groq)`: Classificação por IA com análise contextual (quando API disponível)
    - `Fallback-Heuristic`: Classificação por palavras-chave (fallback automático)
    
    **Respostas:**
    - **200**: Classificação realizada com sucesso
    - **400**: Texto vazio ou inválido
    - **422**: Validação de entrada falhou (texto muito curto ou longo)
    - **500**: Erro interno no servidor
    """

    logger.info(f"Classification request | text_size={len(request.text)} chars")
    
    if not request.text.strip():
        logger.warning("Classification request with empty text")
        raise HTTPException(status_code=400, detail="O texto da mensagem não pode estar vazio.")
    

    try:
        result = await classifier.classify(request.text)
        logger.info(f"Classification completed | category={result.category.value} | strategy={result.strategy} | model={result.model}")
        return result
    
    except Exception as e:
        logger.error(f"Classification endpoint error | error_type={type(e).__name__} | message={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno no servidor de classificação.")




@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Manipulador global de exceções não tratadas.
    
    Args:
        request: Objeto da requisição HTTP.
        exc: Exceção capturada.
    
    Returns:
        JSONResponse: Resposta com status 500 e mensagem de erro.
    """
    logger.critical(f"Unhandled exception | error_type={type(exc).__name__} | message={str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Erro interno inesperado. Contate o suporte."},
    )




if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Uvicorn server | host=0.0.0.0 | port=8000 | app=Nexus Legal Classifier")
    logger.info(f"Startup mode | groq_available={'yes' if settings.GROQ_API_KEY else 'no'} | fallback_mode={'Heuristic' if not settings.GROQ_API_KEY else 'LLM+Heuristic'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)