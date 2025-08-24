import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.temperature,
            google_api_key=settings.llm_key,
        )
        self.llm_pro = ChatGoogleGenerativeAI(
            model=settings.llm_model_pro,
            temperature=settings.temperature,
            google_api_key=settings.llm_key,
        )
    
    async def ainvoke(self, messages, use_pro=False):
        """Async invoke LLM."""
        llm = self.llm_pro if use_pro else self.llm
        try:
            response = await asyncio.to_thread(llm.invoke, messages)
            return response
        except Exception as e:
            logger.error(f"LLM invocation error: {e}")
            raise
    
    async def abind_tools(self, tools, use_pro=False):
        """Async bind tools to LLM."""
        llm = self.llm_pro if use_pro else self.llm
        return llm.bind_tools(tools=tools)