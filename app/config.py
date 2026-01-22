import os
import logging
from dotenv import load_dotenv


load_dotenv()

# Configuração centralizada de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("Settings")



class Settings:
    """
    Gerenciador de configurações da aplicação.
    
    Carrega variáveis de ambiente e define parâmetros da API Groq.
    """
    
    PROJECT_NAME: str = "Nexus Legal Classifier"
    VERSION: str = "1.0.0"
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    GROQ_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"


    def __init__(self) -> None:
        """Inicializa as configurações e valida a presença da chave da API Groq."""

        if not self.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not found. System will run in FALLBACK mode (Heuristic only).")

        else:
            masked_key = f"{self.GROQ_API_KEY[:4]}..." if len(self.GROQ_API_KEY) > 20 else "Invalid"
            logger.info(f"Settings loaded | groq_api_key_detected=yes | key_prefix={masked_key}")



settings = Settings()