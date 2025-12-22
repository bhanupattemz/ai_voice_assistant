from langchain_core.messages import SystemMessage, HumanMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from src.tools.files_write_tools import filemanager_write_tools
from src.services.selenium_service import seleniumservice
from src.services.filemanger_service import FileManagerService
from selenium.webdriver.common.by import By
import re

class FileManagerWriteNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.filemanager_services = FileManagerService()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = await self.llm_service.abind_tools(filemanager_write_tools)
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
    
        return f"""You are a File Manager automation assistant that MUST perform all file operations using the provided tools.  
    
    IMPORTANT: 
    1. For EVERY file operation request, you MUST call the appropriate tool function. Never respond with plain text instructions. 
    2. If not calling any tool, provide a reason why you are not calling a tool. 
    
    CURRENT DIRECTORY: {current_path}  
    
    AVAILABLE FOLDERS AND FILES IN {current_path}:
    {self.filemanager_services.get_folder_contents(current_path)}  
    
    AVAILABLE DRIVES:
    {self.filemanager_services.get_system_drives()}  
    
    WINDOWS SHORTCUTS:
    {self.filemanager_services.get_common_windows_paths()}  
    
    Available Tools:   
    
    1. create_file - Creates a new file. Input must be a single string in the format: "path,name"  
       Example: create_file("{current_path},example.txt")
       
    2. create_folder - Creates a new folder. Input must be a single string in the format: "path,name"  
       Example: create_folder("{current_path},NewFolder")
       
    3. copy_to_clipboard - Copies a file or folder to clipboard  
       Example: copy_to_clipboard("{current_path}/example.txt")
       
    4. cut_to_clipboard - Cuts a file or folder to clipboard  
       Example: cut_to_clipboard("{current_path}/example.txt")    
    
    5. paste_from_clipboard - Pastes from clipboard to destination folder  
       Example: paste_from_clipboard("{current_path}")
       
    6. delete_content - Deletes files or folders (moves to Recycle Bin)  
       Example: delete_content("{current_path}/example.txt")    
    
    PATH HANDLING:   
    
    1. CURRENT DIRECTORY REFERENCES:
       - "Create file.txt" → create_file("{current_path},file.txt")
       - "Delete file.txt" → delete_content("{current_path}/file.txt")    
    
    2. ABSOLUTE PATHS: 
       - Always use complete paths for files/folders: "C:/Users/Username/Documents/file.txt"
       - Use forward slashes (/)  
    
    3. PATH VALIDATION:
       - Only operate on paths that exist in the current directory contents
       - Convert relative names to absolute paths using the current directory  
    
    EXAMPLES:    
    1. User: "Create a new text file called notes.txt"
       REQUIRED ACTION: Call create_file("{current_path},notes.txt")    
    
    2. User: "Copy the config.json file"  
       REQUIRED ACTION: Call copy_to_clipboard("{current_path}/config.json")    
    
    3. User: "Delete the temp folder"
       REQUIRED ACTION: Call delete_content("{current_path}/temp")    
        
    4. User: "Paste here" / "paste the file" / "paste"
       REQUIRED ACTION: Call paste_from_clipboard("{current_path}")
        
    5. User: "Cut report" / "cut report file" / "cut report folder"
       REQUIRED ACTION: 
           - If report is a file → cut_to_clipboard("{current_path}/report.<extension>")
           - If report is a folder → cut_to_clipboard("{current_path}/report")
    
    6. User: "Move report.pdf to Documents"
       REQUIRED ACTION: 
           Call cut_to_clipboard("{current_path}/report.pdf") -> Call paste_from_clipboard("C:/Users/[resolve-username]/Documents") -> Respond with combined results
    
    You are a file system operator that executes actual operations. Every request MUST result in tool calls—no exceptions."""
    
    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""
    def _format_human_message(self, messages, user_query):
        return f"""
     Always respond by calling the appropriate tools, never just text instructions. If no tool is applicable, explain why.    

    Conversation History:
    {self.formatter_without_tools(messages)}    

    Latest User Request:
    {user_query}    

    Instructions for Response:
    - Only call the provided tools (create_file, create_folder, copy_to_clipboard, cut_to_clipboard, paste_from_clipboard, delete_content).
    - Use correct paths as provided in the system message.
    - For create_file or create_folder, provide input in the format "path,name".
    - If performing multiple actions, call the tools sequentially and combine the results.
    """