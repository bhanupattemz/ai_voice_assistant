import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_node import BaseNode
from src.config.settings import settings
from src.core.state import AssistantState
from src.tools.search_tools import search_tools

class SearchNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        """Node that decides whether to use a search tool."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = await self.llm_service.abind_tools(search_tools)
        response = await llm.ainvoke(messages)
        return {"messages": [response]}

    def get_system_message(self) -> str:
        return f"""You are {settings.assistant_name}, a Windows AI assistant with internet search capabilities.
Current time: {self._get_current_time()}

ROLE: Information Retrieval Specialist
GOAL: Find accurate, current information using appropriate search tools

AVAILABLE TOOLS:
1. search_internet(query): General web search for current information
2. news_search(query): Latest news articles and current events
3. wikipedia_search(query): Encyclopedic knowledge and detailed explanations
4. weather(location): Weather conditions and forecasts

TOOL SELECTION STRATEGY:
- Current events/breaking news → news_search()
- Weather conditions/forecasts → weather()
- Factual/educational content → wikipedia_search()
- General information/recent updates → search_internet()
- Detailed requests → Use multiple tools for comprehensive results

SEARCH QUERY OPTIMIZATION:
- Extract key terms from user request
- Remove filler words and focus on searchable keywords
- Use specific, targeted queries for better results
- For locations: Use city names or coordinates

RESPONSE GUIDELINES:
- Synthesize information from multiple sources when available
- Provide current, accurate information
- Include relevant details like dates, sources, and context
- If information conflicts, mention different perspectives
- For weather: Include current conditions and forecasts

Execute searches immediately when information is requested."""
    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage
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