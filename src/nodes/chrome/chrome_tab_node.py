import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging

from src.tools.chrome_tab_tools import chrome_tab_tools
from src.services.selenium_service import seleniumservice

logger = logging.getLogger(__name__)


class ChromeTabNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state: AssistantState) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        if not user_query:
            return {
                "messages": [
                    AIMessage(
                        content="I didn't receive a clear request. Please tell me what you'd like me to do with the browser tabs."
                    )
                ]
            }

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=human_msg),
        ]

        llm_with_tools = await self.llm_service.abind_tools(tools=chrome_tab_tools)
        response = await llm_with_tools.ainvoke(messages)

        return {
            "messages": [response],
        }

    def get_system_message(self) -> str:
        """Generate system message with current browser state and instructions"""
        
        browser_state = self._get_detailed_browser_state()

        return f"""You are a Chrome browser tab management assistant. Your task is to identify the correct tab based on user descriptions and perform the requested actions.

{browser_state}

AVAILABLE TOOLS:
1. switch_tab - Input: tab index (0-based integer)
2. new_tab - Input: URL string 
3. close_tab - Input: tab index (0-based integer)

TAB IDENTIFICATION RULES:
- When user mentions content/website name (e.g., "close youtube", "remove google"):
  → Find the tab containing that content and use its index
  → If multiple tabs match, choose the first one
  → If none match exactly, choose the closest match

- When user mentions position (e.g., "close tab one", "remove first tab", "close tab 2"):
  → "tab one"/"first tab" = index 0
  → "tab two"/"second tab" = index 1  
  → "tab 2" = index 1 (convert human counting to 0-based)
  
- When user says "this tab"/"current tab":
  → Use the index of the currently active tab (marked with CURRENT)

- When user says search in new tab (eg:"search for youtube","open gfg","chandrayaan 3")
  -> "search for youtube" = url https://www.google.com/search?q=search+for+youtube
  -> "open gfg" = url https://www.google.com/search?q=gfg
  -> "chandrayaan 3" = url https://www.google.com/search?q=chandrayaan+3

IMPORTANT:
- ALWAYS provide the exact tab index number (0-based) when using tools
- Double-check the tab list above before choosing an index
- If unsure, pick the most logical match based on user intent
- for new tab only give url like https://www.google.com/

RESPONSE FORMAT:
- Execute the action using the appropriate tool
- Confirm what was done with specific details (e.g., "Closed tab 2: 'YouTube - Video Title'")"""

        
    def _get_detailed_browser_state(self) -> str:
        """Get detailed browser state information for LLM decision making"""
        try:
            tabs = seleniumservice.chrome_driver().window_handles
            current_window = seleniumservice.chrome_driver().current_window_handle

            if not tabs:
                return "CURRENT BROWSER STATE: No tabs are open."

            tabs_info = [f"CURRENT BROWSER STATE: {len(tabs)} tabs open"]
            tabs_info.append("\nTAB LIST (for reference):")

            original_window = current_window
            for i, tab in enumerate(tabs):
                try:
                    seleniumservice.chrome_driver().switch_to.window(tab)
                    title = seleniumservice.chrome_driver().title or "Untitled"
                    url = seleniumservice.chrome_driver().current_url or "No URL"
                    domain = ""
                    if "://" in url:
                        domain = url.split("://")[1].split("/")[0].replace("www.", "")

                    is_current = " ← CURRENT TAB" if tab == current_window else ""

                    tabs_info.append(
                        f"  Index {i}: '{title}' | {domain} | {url}{is_current}"
                    )

                except Exception as e:
                    tabs_info.append(f"  Index {i}: Error accessing tab - {str(e)}")
            try:
                seleniumservice.chrome_driver().switch_to.window(original_window)
            except:
                pass

            tabs_info.append(
                "\nNOTE: Use the Index number (0-based) when calling tools!"
            )
            return "\n".join(tabs_info)

        except Exception as e:
            return f"CURRENT BROWSER STATE: Error getting browser state - {str(e)}"

    def _extract_latest_user_query(self, messages: List) -> str:
        """Extract the latest user message"""
        try:
            for i in range(len(messages) - 1, -1, -1):
                message = messages[i]
                if isinstance(message, HumanMessage):
                    return message.content.strip()
            return ""
        except Exception as e:
            logger.error(f"Error extracting user query: {str(e)}")
            return ""

    def _format_human_message(self, messages: List, user_query: str) -> str:
        """Format the human message with context"""

        return f"""USER REQUEST: "{user_query}"

TASK: Analyze the user's request and identify which tab they want to interact with based on the tab list above.

EXAMPLES OF USER REQUESTS AND EXPECTED ACTIONS:
- "close youtube" → Find tab with YouTube in title/URL, use close_chrome_tab with that index
- "remove google" → Find tab with Google in title/URL, use close_chrome_tab with that index  
- "close tab one" → Use close_chrome_tab with index 0
- "remove first tab" → Use close_chrome_tab with index 0
- "close tab 2" → Use close_chrome_tab with index 1 (tab 2 in human terms = index 1)
- "switch to github" → Find tab with GitHub, use switch_chrome_tab with that index
- "open reddit.com" → Use open_new_chrome_tab with "reddit.com"

This the user conversation:
{self.formatter_without_tools(messages)}
Now execute the appropriate action for the user's request: {user_query}"""
