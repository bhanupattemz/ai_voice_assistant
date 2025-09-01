import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.core.state import AssistantState
from src.services.llm_service import LLMService
from src.utils.conversation import ConversationFormatter
from datetime import datetime
from zoneinfo import ZoneInfo
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class CalendarBaseNode(ABC):
    """Base class for all nodes in the assistant graph."""

    def __init__(self, config=None):
        self.SCOPES = ["https://www.googleapis.com/auth/calendar"]
        self.ConversationFormatter = ConversationFormatter()
        self.llm_service = LLMService()
        self.config = config or {}
        self.formatter = self.ConversationFormatter.format_conversation
        self.formatter_without_tools = self.ConversationFormatter.format_conversation_without_tools
        

    @abstractmethod
    def execute(self, state: AssistantState) -> Dict[str, Any]:
        """Execute the node's logic synchronously."""
        pass

    def _get_current_time(self):
        return datetime.now(ZoneInfo("Asia/Kolkata"))

    def get_calendar_service(self):
        creds = None
        if os.path.exists("token.pkl"):
            with open("token.pkl", "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.pkl", "wb") as token:
                pickle.dump(creds, token)
        service = build("calendar", "v3", credentials=creds)
        return service
    
    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage
        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

