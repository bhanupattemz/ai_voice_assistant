import os
from dotenv import load_dotenv
load_dotenv(override=True)



class Settings:
    def __init__(self):
        self.llm_model: str = os.getenv("LLM_MODEL")
        self.llm_model_pro: str =os.getenv("LLM_MODEL_PRO")
        self.llm_key: str = os.getenv("LLM_KEY")
    
        # API Keys
        self.news_api_key=os.getenv("NEWS_API_KEY")
        self.serper_api_key=os.getenv("SERPER_API_KEY")
    
        # Assistant Configuration
        self.assistant_name=os.getenv("NAME")
        self.temperature=0.7
        self.timezone=os.getenv("TZ")
    
        # Google Calendar
        self.token_file="token.json"
        self.credentials_file="credentials.json"


settings = Settings()

