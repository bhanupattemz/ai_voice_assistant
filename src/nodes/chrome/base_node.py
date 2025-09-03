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
        self.ConversationFormatter = ConversationFormatter()
        self.llm_service = LLMService()
        self.config = config or {}
        self.formatter = self.ConversationFormatter.format_conversation
        self.formatter_without_tools = self.ConversationFormatter.format_conversation_without_tools
        self.ALL_KEYS = [
            *[chr(i) for i in range(97, 123)],
            *[str(i) for i in range(10)],
            *[f"f{i}" for i in range(1, 13)],
            "shift",
            "shiftleft",
            "shiftright",
            "ctrl",
            "ctrlleft",
            "ctrlright",
            "alt",
            "altleft",
            "altright",
            "winleft",
            "winright",
            "command",
            "option",
            "up",
            "down",
            "left",
            "right",
            "home",
            "end",
            "pagedown",
            "pageup",
            "backspace",
            "delete",
            "insert",
            "tab",
            "enter",
            "space",
            "esc",
            "escape",
            "capslock",
            "numlock",
            "scrolllock",
            "pause",
            "printscreen",
            "apps",
            "menu",
            "numpad0",
            "numpad1",
            "numpad2",
            "numpad3",
            "numpad4",
            "numpad5",
            "numpad6",
            "numpad7",
            "numpad8",
            "numpad9",
            "multiply",
            "add",
            "separator",
            "subtract",
            "decimal",
            "divide",
            "volumemute",
            "volumedown",
            "volumeup",
            "playpause",
            "prevtrack",
            "nexttrack",
        ]

    
        

    @abstractmethod
    def execute(self, state: AssistantState) -> Dict[str, Any]:
        """Execute the node's logic synchronously."""
        pass

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
