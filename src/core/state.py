from typing import Annotated, TypedDict, List, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AssistantState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    context: dict
    user_preferences: dict
