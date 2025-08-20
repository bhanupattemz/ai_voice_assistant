from langchain_core.messages import SystemMessage, HumanMessage
from .base_node import BaseNode
from src.config.settings import settings
from src.core.state import AssistantState


class ChatbotNode(BaseNode):
    def __init__(self):
        super().__init__()

    def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        response = self.llm_service.invoke(messages)

        return {"messages": [response]}

    def get_system_message(self) -> str:
        return f"""
        You are {settings.assistant_name}, an AI voice assistant for Windows.
        Current time: {self._get_current_time()}
        Guidelines:
        - Keep responses conversational and under 30 seconds when spoken
        - Always confirm before making system changes
        - Be helpful, friendly, and efficient
        - Remember conversation context
        """

    def _extract_latest_user_query(self, messages):
        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""
        You are an AI Assistant.
        The complete conversation history between the assistant and user is:
        {self.formatter(messages)}
        The user's most recent request is: "{user_query}"
        Based on the conversation context and any tool results or AI responses that have already been provided, please generate an appropriate response to the user's latest request.
        """
