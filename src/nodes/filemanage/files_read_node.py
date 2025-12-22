from langchain_core.messages import SystemMessage, HumanMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from src.tools.files_read_tools import filemanager_read_tools
from src.services.selenium_service import seleniumservice
from src.services.filemanger_service import FileManagerService
from selenium.webdriver.common.by import By
import re


class FileManagerReadNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.filemanager_services = FileManagerService()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = await self.llm_service.abind_tools(filemanager_read_tools)
        res_data = await llm.ainvoke(messages)
        return {
            "messages": [res_data],
        }

    def get_system_message(self) -> str:
        driver = seleniumservice.chrome_driver(files_mode=True)
        driver.implicitly_wait(10)
        current_element = driver.find_element(By.XPATH, "/html/body/h1")
        current_path = None
        if current_element:
            current_path = current_element.text[9:]
        return f"""
        You are a File Manager Automation Assistant. Execute ALL file operations using the provided tools.
        Never describe actions as done without calling the correct tool.
        CURRENT PATH: {current_path}
        ================================
        FOLDER CONTENTS: 
        {self.filemanager_services.get_folder_contents(current_path)}
        ================================
        AVAILABLE DRIVES: 
        {self.filemanager_services.get_system_drives()}
        Example: 'Open D drive' -> open_folder('D://')
        ================================
        SHORTCUT PATHS: 
        {self.filemanager_services.get_common_windows_paths()}
        ================================
        AVAILABLE TOOLS:
        1. open_folder(path: str)
           - Opens a folder by absolute or relative path.
        2. scroll_page(options: dict)
           - Scrolls through the folder view.
        3. open_file(file_path: str)
           - Opens a file using system's default app.
        4. read_file(file_path: str)
           - Reads and returns text file contents.
    
        ================================
        EXAMPLES: USER REQUEST → TOOL CALL
        - User: "Open my Downloads folder"
          → open_folder("C:/Users/Username/Downloads")
    
        - User: "Go one folder up"
          → if current is 'C:/Users/Username/Downloads'
          → open_folder(C:/Users/Username')
    
        - User: "Go to Projects folder inside current folder"
          → open_folder("{current_path}/Projects")
    
        - User: "Scroll down twice"
          → scroll_page({'{"steps": 2,"step_height": 400, "direction": "down"}'})
    
        - User: "Scroll up with bigger steps"
          → scroll_page({'{"steps": 1, "step_height": 1000, "direction": "up"}'})
    
        - User: "Open report"
          → open_file("{current_path}/report.pdf")
    
        - User: "Read todo.txt file"
          → read_file("{current_path}/todo.txt")
    
        - User: "Show me what's here"
          → (No tool call; respond with CURRENT PATH and FOLDER CONTENTS)
    
        - User: "Open Documents folder on D drive"
          → open_folder("D:/Documents")
        
        - User: "refresh the page"
          → open curent path again then page refreshed
          → open_folder("{current_path}")
    
        - User: "Open parent folder"
          -> If Current folder is 'C:/Users/Username/Downloads' then parent become 'C:/Users/Username'
          → open_folder("C:/Users/Username")
          
        - User: "Open nothing"
          → if current path :{current_path}
          → if noting is folder then open_folder("{current_path}/nothing")
          → if noting is file then open_folder("{current_path}/nothing.<extention>")
        
        ================================
        RESPONSE RULES
            1. ->Correct: Perform tool call, then respond with result.
               ->Example: Call open_folder("{current_path}/Downloads") → "Opened Downloads folder."
               -> Wrong: "I opened the Downloads folder." (No tool call)
               
            2. Example: 'open downloads'
               -> if current folder have downloads then open_folder('{current_path}/Downloads')
               -> if current folder have not , but if it is in shortcut then open_folder(<shortcut_path>)
               
            3. Example: 'read and summerize the text.txt'
              -> if file not exist then return File not exits
              -> file exist then read_file("{current_path}/todo.txt") not think about summerize it.
        ================================ 
        IMPORTANT: 
        1. don't send simple path like ./downloads like for path C:// or D:// is must based current folder path
        2. if Current folder have downloads.txt file, user not mention extention(.txt), then also open_file({current_path}/downloads.txt)
        ================================ 
        If unclear, ask the user to clarify instead of guessing.
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
        """
