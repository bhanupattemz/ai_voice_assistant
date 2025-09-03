from langchain_core.messages import AIMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from src.services.selenium_service import seleniumservice

class ChromeCloseNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        try:
            seleniumservice.chrome_driver().quit()
        except Exception as e:
            return {"messages": [AIMessage(content=f"Error occurs: {e}")]}

        return {
            "mode": "normal",
            "messages": [
                AIMessage(
                    content="chrome window close success and exited from chrome mode."
                )
            ],
        }
