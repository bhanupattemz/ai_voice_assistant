import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.core.state import AssistantState
from src.services.llm_service import LLMService
from src.utils.conversation import ConversationFormatter
from datetime import datetime
from zoneinfo import ZoneInfo

class BaseNode(ABC):
    """Base class for all nodes in the assistant graph."""
    
    def __init__(self, config=None):
        self.llm_service = LLMService()
        self.config = config or {}
        self.formatter = ConversationFormatter().format_conversation
    
    @abstractmethod
    def execute(self, state: AssistantState) -> Dict[str, Any]:
        """Execute the node's logic synchronously."""
        pass
    
    
    def get_system_message(self) -> str:
        """Get the system message for this node."""
        return "You are a helpful AI assistant."
    
    def _get_current_time(self):
        return datetime.now(ZoneInfo("Asia/Kolkata"))
    
    def execute_sync_wrapper(self, state: AssistantState) -> Dict[str, Any]:
        """Wrapper to run async execute in sync context."""
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.aexecute(state))
                return future.result()
        except RuntimeError:
            return asyncio.run(self.aexecute(state))