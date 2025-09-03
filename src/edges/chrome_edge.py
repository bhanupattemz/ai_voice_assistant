import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_edge import BaseEdge
from src.config.settings import settings

class ChromeRedirectorEdge(BaseEdge):
    def __init__(self):
        super().__init__()

    async def execute(self, state):
        """Edge that routes to chatbot or a specific Chrome node."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query, state)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

        try:
            response = await self.llm_service.ainvoke(messages, use_pro=True)
            result = response.content.strip().lower()

            valid_nodes = {"chatbot", "chrome_close_node", "chrome_tab_node"}

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
1. **chatbot** - only when current mode is normal or when chrome mode is exited.
2. **chrome_close_node** - if user wants to close the chrome window.
3. **chrome_tab_node** - if user wants modification related to chrome tabs.

Instructions:
- Carefully read the latest user message.
- If the user explicitly says the current mode is normal or mentions "Chrome Mode exited", return **chatbot**.
    - Close Chrome window → chrome_close_node
    - Tab modifications → chrome_tab_node
- Return only the node name in lowercase.
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
Please select the correct path: "chatbot", "chrome_close_node","chrome_tab_node".
"""
