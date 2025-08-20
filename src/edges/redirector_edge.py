from langchain_core.messages import SystemMessage, HumanMessage
from .base_edge import BaseEdge


class RedirectorEdge(BaseEdge):
    def __init__(self):
        super().__init__()

    def execute(self, state):
        """Node that decides whether to use a calendar tool."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        response = self.llm_service.invoke(messages, use_pro=True)
        result = response.content.strip().lower()
        nodes = ["chatbot", "network_search", "calendar_node", "browser_node"]
        print(result)
        if result in nodes:
            return result
        return "chatbot"

    def get_system_message(self) -> str:
        return """
        You are a flow redirector that analyzes user requests and determines the next action.
        
        Respond with ONLY ONE of these exact words:
        - network_search (if the user needs internet search, weather, news, wikipedia search, 
        useful when user want some detailed information/small information related to anything)
        - END (if the request is complete or no further action is needed)
        - chatbot (if the request is general question where it can normally done by llm without above nodes)
        - calendar_node (if user want to perform operations related to Calendar, like create events meeting, and all related to events in calendar)
        - browser_node (if user want to perform operations related to Browser)
        Return only the single word, nothing else.
        """

    def _extract_latest_user_query(self, messages):
        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""
        You are an agent that analyzes user requests and determines the next action.
        
        The complete conversation history between the assistant and user is:
        {self.formatter(messages)}
        The user's latest message is: {user_query}
        Instructions:
        - If the user's request has already been completed and they are not asking to rerun the task, respond with "chatbot"
        - Otherwise, analyze the user's request and determine the appropriate next action:
        - compare the last message from user with previous messages. it may need to use same node that the time. 
        Respond with only one word
        """
