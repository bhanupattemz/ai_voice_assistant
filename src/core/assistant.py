from src.core.graph_builder import GraphBuilder
from langchain_core.messages import HumanMessage
class VoiceAssistant:
    def __init__(self):
        self.graph_builder = GraphBuilder()
        self.graph = None

    async def initialize(self):
        self.graph = await self.graph_builder.build()
    
    
    async def chat(self, message: str, config: dict = None) -> str:
        """Process a chat message asynchronously and return response."""  
        if config is None:
            config = {"configurable": {"thread_id": "1"}}
        
        state = {
            "messages": [HumanMessage(content=message)],
            "context": {},
            "user_preferences": {},
            "feedback":"",
            "mode":"normal"
        }
        
        result = await self.graph.ainvoke(state, config)
        return result["messages"][-1].content
    
   
