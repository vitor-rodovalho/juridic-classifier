import httpx
import json
import logging
from config import settings
from schemas import CategoryEnum, ClassificationResponse
from resources import KEYWORDS, SYSTEM_PROMPT_TEMPLATE




# Configura logger
logger = logging.getLogger(__name__)



class Classifier:
    """Classificador de mensagens jurídicas usando LLM ou heurísticas."""
    
    def __init__(self) -> None:
        """Inicializa o classificador carregando base de palavras-chave."""

        self.keywords = KEYWORDS
        logger.debug("Classifier inicializado com sucesso.")



    async def classify(self, text: str) -> ClassificationResponse:
        """
        Tenta classificar texto via LLM (Groq). Se falhar, usa heurística local.
        
        Args:
            text: Texto jurídico a ser classificado.
        
        Returns:
            ClassificationResponse: Resposta contendo categoria e raciocínio.
        """
        
        if not settings.GROQ_API_KEY:
            logger.warning("API Key não encontrada. Iniciando Fallback local.")
            return self._heuristic_classify(
                text, 
                reason="API Key do Groq não configurada. Fallback com heurística local ativado."
            )

        try:
            logger.debug("Iniciando chamada ao Groq API...")
            return await self._call_groq_llm(text)
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP do Groq: status_code={e.response.status_code}")
            return self._heuristic_classify(text, reason=f"Erro HTTP na IA ({e.response.status_code}).")
        
        except Exception as e:
            logger.warning(f"Falha na conexão com LLM: {type(e).__name__}: {str(e)}. Ativando Fallback local.")
            return self._heuristic_classify(
                text, 
                reason="Indisponibilidade momentânea da IA."
            )



    async def _call_groq_llm(self, text: str) -> ClassificationResponse:
        """
        Realiza chamada assíncrona à API do Groq para classificação via LLM.
        
        Args:
            text: Texto jurídico a ser classificado.
        
        Returns:
            ClassificationResponse: Resposta com categoria e raciocínio da IA.
        
        Raises:
            httpx.HTTPStatusError: Se a resposta HTTP indicar erro.
        """
        
        categories_list = ", ".join([cat.value for cat in CategoryEnum])
        formatted_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(categories=categories_list)

        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": formatted_system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }


        async with httpx.AsyncClient() as client:
            start_time = logging.time.time()
            response = await client.post(
                settings.GROQ_URL, 
                json=payload, 
                headers=headers, 
                timeout=8.0
            )
            response.raise_for_status()
            duration = logging.time.time() - start_time
            
            logger.info(f"Groq API success | duration={duration:.2f}s | status_code=200")
            logger.debug(f"Processing JSON response from Groq API...")
            
            data = response.json()
            content = json.loads(data['choices'][0]['message']['content'])
            
            cat_str = content.get("category", "Outros")
            
            category_enum = next(
                (c for c in CategoryEnum if c.value.lower() == cat_str.lower()), 
                CategoryEnum.OUTROS
            )

            logger.debug(f"Parsed category from LLM: category={category_enum.value}")

            return ClassificationResponse(
                category=category_enum,
                reasoning=content.get("reasoning", "Classificação via IA"),
                model=settings.GROQ_MODEL,
                strategy="LLM (Groq)"
            )



    def _heuristic_classify(self, text: str, reason: str) -> ClassificationResponse:
        """
        Classifica texto usando heurística baseada em palavras-chave.
        
        Args:
            text: Texto jurídico a ser classificado.
            reason: Motivo pela qual o fallback foi acionado.
        
        Returns:
            ClassificationResponse: Resposta com categoria identificada e raciocínio.
        """

        logger.info("Executando classificação heurística (Regras).")
        
        text_lower = text.lower()
        best_category = CategoryEnum.OUTROS
        max_matches = 0

        for category, terms in self.keywords.items():
            matches = sum(1 for term in terms if term in text_lower)
            if matches > max_matches:
                max_matches = matches
                best_category = category

        final_reason = (
            f"{reason} Identificados {max_matches} termos chave utilizando heurísticas." 
            if max_matches > 0 
            else f"{reason} Nenhum termo chave relevante identificado utilizando heurísticas."
        )

        logger.info(f"Heuristic classification completed | category={best_category.value} | matches={max_matches}")

        return ClassificationResponse(
            category=best_category,
            reasoning=final_reason,
            model="Keywords-Heuristic",
            strategy="Fallback-Heuristic"
        )