from langchain_core.messages import SystemMessage, HumanMessage
from .base_node import BaseNode
from src.config.settings import settings
from src.core.state import AssistantState
from src.tools.search_tools import search_tools


class SearchNode(BaseNode):
    def __init__(self):
        super().__init__()

    def execute(self, state) -> AssistantState:
        """Node that decides whether to use a calendar tool."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = self.llm_service.bind_tools(search_tools)
        response = llm.invoke(messages)
        return {"messages": [response]}

    def get_system_message(self) -> str:
        return f"""
        You are {settings.assistant_name}, an AI voice assistant for Windows.
        Current time: {self._get_current_time()}. 
        Use the search tool when you need to find Search any thing on internet.
        Use the news Tool with query to get the top news related to that query if user ask for new use this tool.
        if user mentioned to search on Wikipedia use Wikipedia tool for searching.
        If user ask details related to weather use weather Tool for that.
        Provide helpful and accurate responses based on the search results.
        if user ask for more detailed about any thing search both news and internet for data.
        """

    def _extract_latest_user_query(self, messages):
        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""
        You are an AI assistant that can search the internet using available tools.\\
        The entire conversation with the assistant, with the user's original request and all replies, is:
        {self.formatter(messages)}\\
        This is the latest respound from the user:
        {user_query}
        """
