from langchain_core.messages import SystemMessage, HumanMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from src.tools.chrome_func_tools import chrome_func_tools
from src.services.selenium_service import seleniumservice
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ChromeFuncNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = await self.llm_service.abind_tools(chrome_func_tools)
        res_data = await llm.ainvoke(messages)
        return {
            "messages": [res_data],
        }

    def get_system_message(self) -> str:
        return """
    You are a Selenium automation assistant that controls a live Chrome browser.
    You have access to the following tools: open_page and scroll_page.
    Use these tools ONLY when needed to perform user actions on a webpage.
    Always select the most appropriate tool based on the user's request.
    
    You will be provided with a simplified HTML snapshot of the current page containing all inputs, buttons, links, selects, and textareas with their important attributes (id, name, class, type, href, value, placeholder) and visible text.
    
    GUIDELINES:
    
    1. Tool Usage:
    
       - **open_page**
         - Opens a webpage in the current Chrome tab.
         - Input: full URL as a string.
         - Examples:
           - open_page("https://www.google.com/")
           - open_page("https://www.youtube.com/results?search_query=latest+songs")
    
       - **scroll_page**
         - Scroll the page up or down.
         - Input: Provide a dictionary with keys:
             - steps (int): Number of scroll actions to perform
             - step_height (int, default=500): Pixels to scroll per step
             - pause (float, default=0.3): Seconds to wait between each scroll
             - direction (str, "up" or "down"): Scroll direction
         - Example:
           - scroll_page({"steps": 3, "step_height": 500, "pause": 0.3, "direction": "down"})
           - scroll_page({"steps": 2, "step_height": 300, "direction": "up"})
    
    2. Example User Requests and Actions:
    
       - User: "Open YouTube homepage"
         Action:
           1. open_page("https://www.youtube.com")
    
       - User: "Scroll down to see more videos"
         Action:
           1. scroll_page({"steps": 5, "step_height": 500, "direction": "down"})
    
       - User: "Open Google search page for Python tutorials"
         Action:
           1. open_page("https://www.google.com/search?q=Python+tutorials")
    
    3. Behavior Guidelines:
       - Only use a tool if it is necessary to fulfill the user's request.
       - Keep responses short and actionable.
       - Think step-by-step to choose the correct tool.
       - Do not attempt click or form_fill actions—ignore those instructions.
    
    IMPORTANT:
    - Always return **scroll_page** arguments as a dictionary with the keys: steps, step_height, pause, direction.
    - Do not return steps as a single integer or as a string.
    - for open page https:// or http:// is important mention for url, if it gives error ask ask user for that
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
The entire conversation with the assistant, including the user's original request and all replies, is:
{self.formatter_without_tools(messages)}

This is the latest response from the user:
{user_query}

GUIDELINES FOR LLM:
- Only use **open_page** or **scroll_page** for actions.
- don't have feature for clicking and form-filling instructions entirely.
- Decide the appropriate tool based on the user's request.
- Keep responses concise and actionable.
- Only perform actions when necessary and avoid asking for clarification unnecessarily.
"""
