from src.core.graph_builder import GraphBuilder
from langchain_core.messages import HumanMessage
class VoiceAssistant:
    def __init__(self):
        self.graph_builder = GraphBuilder()
        self.graph=self.graph_builder.build()
    
    def chat(self, message: str, config: dict = None) -> str:
        """Process a chat message and return response."""
        
        if config is None:
            config = {"configurable": {"thread_id": "1"}}
        
        state = {
            "messages": [HumanMessage(content=message)],
            "context": {},
            "user_preferences": {}
        }
        
        result = self.graph.invoke(state, config=config)
        return result["messages"][-1].content