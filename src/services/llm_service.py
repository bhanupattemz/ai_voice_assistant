from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.settings import settings

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
    
    def invoke(self, messages, use_pro=False):
        llm = self.llm_pro if use_pro else self.llm
        return llm.invoke(messages)
    
    def bind_tools(self, tools, use_pro=False):
        llm = self.llm_pro if use_pro else self.llm
        return llm.bind_tools(tools=tools)