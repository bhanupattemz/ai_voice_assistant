import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from pydantic import BaseModel, Field


class DataOutput(BaseModel):
    next_mode: str = Field(description="next mode of the user")


class KeyboardNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = self.llm_service.llm.with_structured_output(DataOutput)
        res_data = await llm.ainvoke(messages)
        mode = res_data.next_mode
        if mode == "keyboard":
            return {
                "mode": res_data.next_mode,
                "messages": [AIMessage(content="enter into Keyboard mode success.")],
            }
        return {
            "mode": res_data.next_mode,
            "messages": [AIMessage(content="Keyboard mode has been exited.")],
        }

    def get_system_message(self) -> str:
        return """
        You are a mode classifier for an AI assistant. Your job is to determine
        whether the assistant should remain in 'keyboard' mode or switch to 'normal' mode
        based on the user's latest message.    

        Available modes:
        - "keyboard": The assistant is currently in keyboard mode. Stay in this mode if the user
          is still typing, interacting, or has not explicitly asked to exit keyboard mode.
        - "normal": Switch to this mode ONLY if the user clearly indicates they want to stop typing,
          exit keyboard mode, or finish the current task.    

        Instructions:
        1. Analyze the latest user message carefully.
        2. If the user says anything like "exit", "done", "finish", "stop typing",
           or similar, return "normal".
        3. Otherwise, always return "keyboard".
        4. Be strict: Only switch to "normal" when the intention is clear.    

        Respond ONLY with the next_mode field, containing either "keyboard" or "normal".
        """

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""
        The entire conversation with the assistant, with the user's original request and all replies, is:
        {self.formatter_without_tools(messages)}\\
        This is the latest respound from the user:
        {user_query}
        """
