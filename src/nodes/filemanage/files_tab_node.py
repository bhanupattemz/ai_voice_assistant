import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging
from src.tools.files_tab_tools import file_manager_tab_tools
from src.services.selenium_service import seleniumservice
from src.services.filemanger_service import FileManagerService
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class FileManagerTabNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.filemanager_services = FileManagerService()

    async def execute(self, state: AssistantState) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        if not user_query:
            return {
                "messages": [
                    AIMessage(
                        content="I didn't receive a clear request. Please tell me what you'd like me to do with the File Manager windows."
                    )
                ]
            }

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=human_msg),
        ]

        llm_with_tools = await self.llm_service.abind_tools(
            tools=file_manager_tab_tools
        )
        response = await llm_with_tools.ainvoke(messages)

        return {
            "messages": [response],
        }

    def get_system_message(self) -> str:
        """Generate system message with current File Manager state and instructions"""

        fm_state = self._get_detailed_filemanager_state()
        driver = seleniumservice.chrome_driver(files_mode=True)
        driver.implicitly_wait(10)
        current_element = driver.find_element(By.XPATH, "/html/body/h1")
        current_path = None
        if current_element:
            current_path = current_element.text.split(" ")[2]
        return f"""You are a File Manager assistant. Your task is to identify the correct File Manager tab based on user descriptions and perform the requested actions.
        {fm_state}
        ---
        CURRENT PATH: {current_path}
            
        ---
        
        AVAILABLE FOLDERS AND FILES:
        {self.filemanager_services.get_folder_contents(current_path)}
        
        ---
        
        AVAILABLE DRIVES:
        {self.filemanager_services.get_system_drives()}
        Example: "open D drive" → new_tab("D:/")
        
        ---
        
        COMMON SHORTCUT PATHS:
        {self.filemanager_services.get_common_windows_paths()}
        Example: "open Downloads" → new_tab("<DownloadsPath>")
        
        ---
        AVAILABLE TOOLS:
        1. switch_tab - Input: tab index (0-based integer)
        2. new_tab - Input: folder path string 
        3. close_tab - Input: tab index (0-based integer)
        
        TAB IDENTIFICATION RULES:
        - When user mentions folder name (e.g., "close Documents", "open Downloads"):
          → Find the tab showing that folder and use its index
          → If multiple tabs match, choose the first one
          → If none match exactly, choose the closest match
        
        - When user mentions position (e.g., "close first tab", "remove tab two"):
          → "first tab" = index 0
          → "second tab" = index 1  
          → "tab 2" = index 1 (convert human counting to 0-based)
          
        - When user says "this tab"/"current tab":
          → Use the index of the currently active tab (marked with CURRENT)
        
        IMPORTANT:
        - ALWAYS provide the exact tab index number (0-based) when using tools
        - Double-check the tab list above before choosing an index
        - If unsure, pick the most logical match based on user intent
        - For new_tab only give a local folder path (do NOT add http:// or https://)
        - Don't open file in new tab
        
        RESPONSE FORMAT:
        - Execute the action using the appropriate tool
        - Confirm what was done with specific details (e.g., "Closed tab 2: 'Documents'")"""

    def _get_detailed_filemanager_state(self) -> str:
        """Get detailed File Manager state information for LLM decision making"""
        try:
            windows = seleniumservice.chrome_driver(files_mode=True).window_handles
            current_window = seleniumservice.chrome_driver(
                files_mode=True
            ).current_window_handle

            if not windows:
                return "CURRENT FILE MANAGER STATE: No windows are open."

            windows_info = [f"CURRENT FILE MANAGER STATE: {len(windows)} windows open"]
            windows_info.append("\nWINDOW LIST (for reference):")

            original_window = current_window
            for i, window in enumerate(windows):
                try:
                    seleniumservice.chrome_driver(files_mode=True).switch_to.window(
                        window
                    )
                    title = (
                        seleniumservice.chrome_driver(files_mode=True).title
                        or "Untitled"
                    )
                    url = (
                        seleniumservice.chrome_driver(files_mode=True).current_url
                        or "No Path"
                    )

                    is_current = " ← CURRENT WINDOW" if window == current_window else ""
                    windows_info.append(f"  Index {i}: '{title}' | {url}{is_current}")

                except Exception as e:
                    windows_info.append(
                        f"  Index {i}: Error accessing window - {str(e)}"
                    )
            try:
                seleniumservice.chrome_driver(files_mode=True).switch_to.window(
                    original_window
                )
            except:
                pass

            windows_info.append(
                "\nNOTE: Use the Index number (0-based) when calling tools!"
            )
            return "\n".join(windows_info)

        except Exception as e:
            return f"CURRENT FILE MANAGER STATE: Error getting windows state - {str(e)}"

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

TASK: Analyze the user's request and identify which File Manager window they want to interact with based on the window list above.

EXAMPLES OF USER REQUESTS AND EXPECTED ACTIONS:
- "close Documents" → Find window with 'Documents' in title/path, use close_window with that index
- "open Downloads" → Find or open a new window at Downloads, use new_window
- "close first window" → Use close_window with index 0
- "remove window two" → Use close_window with index 1
- "switch to Pictures" → Find window with 'Pictures', use switch_window with that index

This is the user conversation:
{self.formatter_without_tools(messages)}
Now execute the appropriate action for the user's request: {user_query}"""
