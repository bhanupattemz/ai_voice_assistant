import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_edge import BaseEdge
from src.config.settings import settings


class FileManagerRedirectorEdge(BaseEdge):
    def __init__(self):
        super().__init__()

    async def execute(self, state):
        """Edge that routes to chatbot or a specific File Manager node."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query, state)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

        try:
            response = await self.llm_service.ainvoke(messages, use_pro=True)
            result = response.content.strip().lower()

            valid_nodes = {
                "chatbot",
                "filemanager_close_node",
                "filemanager_tab_node",
                "filemanager_func_node",
            }
            print(result)
            if result in valid_nodes:
                return result

            return "chatbot"

        except Exception as e:
            print(f"Router error: {e}, defaulting to 'chatbot'")
            return "chatbot"

    def get_system_message(self) -> str:
        return """
You are a path selector (router) for the assistant. Your goal is to choose the correct path based on the user's request.

Available paths:
1. **chatbot** - only when current mode is normal or when File Manager mode is exited.
2. **filemanager_close_node** - if user wants to close a File Manager window.
3. **filemanager_tab_node** - if user wants modifications related to File Manager tab (opening, closing, switching windows, or opening a new folder in a window).
4. **filemanager_func_node** - if user wants to perform actions inside a File Manager window, such as scrolling or interacting with folder contents, and it is not related to window management or closing File Manager.

Examples:
- User: "Close the window" → **filemanager_close_node**
- User: "Open a new tab at Downloads folder" → **filemanager_tab_node**
- User: "Switch to the Pictures tab" → **filemanager_tab_node**
- User: "Scroll down to see more files" → **filemanager_func_node**
- User: "Open the Music folder in current window" → **filemanager_func_node**

Instructions:
- Carefully read the latest user message.
- If the user explicitly says the current mode is normal or mentions "File Manager Mode exited", return **chatbot**.
- Close File Manager window → **filemanager_close_node**
- tab modifications → **filemanager_tab_node**
- Perform File Manager actions (scroll, open folder) → **filemanager_func_node**
  -> filemanager_tab_node: open new tab, open folder, switch tab, close tab
  -> filemanager_func_node: if user wants work not related to close_node or tab_node
- Return only the node name in lowercase.
- one window have mutiple tabs

IMPORTANT:
- don't go filemanager_close_node until user says close window
- if user say tab go with filemanager_tab_node*
"""

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""

    def _format_human_message(self, messages, user_query, state):
        return f"""
Conversation so far:
{self.formatter_without_tools(messages)}
Latest user message:
{user_query}
Current Mode: {settings.mode}
Please select the correct path: "chatbot", "filemanager_close_node", "filemanager_tab_node", "filemanager_func_node".
"""
