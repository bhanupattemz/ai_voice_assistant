import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_edge import BaseEdge

class KeyboardRedirectorEdge(BaseEdge):
    def __init__(self):
        super().__init__()

    async def execute(self, state):
        """Edge that routes to chatbot or a specific keyboard node."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query, state)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

        try:
            response = await self.llm_service.ainvoke(messages, use_pro=True)
            result = response.content.strip().lower()

            # Valid targets
            valid_nodes = {"chatbot", "keyboard_hotkey", "keyboard_presskey", "keyboard_write"}

            # Determine the route
            if result in valid_nodes:
                return result
            else:
                # Fallback: try to infer from keywords
                if any(k in user_query.lower() for k in ["press", "hit", "key"]):
                    return "keyboard_presskey"
                elif any(k in user_query.lower() for k in ["hotkey", "shortcut", "ctrl", "alt", "shift"]):
                    return "keyboard_hotkey"
                elif any(k in user_query.lower() for k in ["type", "write", "enter text", "write text"]):
                    return "keyboard_write"
                else:
                    return "chatbot"

        except Exception as e:
            print(f"Router error: {e}, defaulting to 'chatbot'")
            return "chatbot"

    def get_system_message(self) -> str:
        return """
You are a path selector (router) for the assistant. Your goal is to choose the correct path based on the user's request.

Available paths:
1. **chatbot** – only when current mode is normal or when keyboard mode is exited.
2. **keyboard_hotkey** – for multi-key shortcuts (2-3 keys like ctrl+c, alt+tab).
3. **keyboard_presskey** – for single key presses (enter, space, esc, arrow keys).
4. **keyboard_write** – for typing out text strings.

Instructions:
- Carefully read the latest user message.
- If the user explicitly says the current mode is normal or mentions "Keyboard Mode exited", return **chatbot**.
- For keyboard-related requests, select the appropriate node:
    - Multi-key shortcuts → keyboard_hotkey
    - Single key presses → keyboard_presskey
    - Typing text → keyboard_write
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
Current Mode: {state.get("mode", "normal")}
Please select the correct path: chatbot, keyboard_hotkey, keyboard_presskey, or keyboard_write.
"""
