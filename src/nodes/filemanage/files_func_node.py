from langchain_core.messages import SystemMessage, HumanMessage
from src.nodes.base_node import BaseNode
from src.core.state import AssistantState
from src.tools.files_func_tools import filemanager_func_tools
from src.services.selenium_service import seleniumservice
from src.services.filemanger_service import FileManagerService
from selenium.webdriver.common.by import By


class FileManagerFuncNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.filemanager_services = FileManagerService()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = await self.llm_service.abind_tools(filemanager_func_tools)
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
            current_path = current_element.text.split(" ")[2]

        return f"""
        You are a Selenium-powered automation assistant controlling a live File Manager in a browser.
        You can see the current folder, available files, drives, and shortcuts. Use tools ONLY when needed.
        
        CURRENT PATH: {current_path}
        
        ---
        
        AVAILABLE FOLDERS AND FILES:
        {self.filemanager_services.get_folder_contents(current_path)}
        
        ---
        
        AVAILABLE DRIVES:
        {self.filemanager_services.get_system_drives()}
        Example: "open D drive" → open_folder("D:/")
        
        ---
        
        COMMON SHORTCUT PATHS:
        {self.filemanager_services.get_common_windows_paths()}
        Example: "open Downloads" → open_folder("<DownloadsPath>")
        
        ---
        
        TOOLS YOU CAN USE:
        
        1. open_folder
           - Opens a folder in the File Manager.
           - Input: Absolute path (str).
           - Example: open_folder("C:/Users/Username/Documents")
        
        2. scroll_page
           - Scrolls the folder/file view.
           - Input: Dictionary → {{"steps": int, "step_height": int, "pause": float, "direction": "up"|"down"}}
           - Example: scroll_page({{"steps": 3, "step_height": 500, "pause": 0.3, "direction": "down"}})
        
        3. open_file
           - Opens a file with the default system app.
           - Input: "file_path" (str).
           - Example: open_file("C:/Users/Username/Documents/file.txt")
        
        4. copy_to_clipboard
           - Copies a file or folder path.
           - Input: "path" (str).
           - Example: copy_to_clipboard("C:/Users/Username/Documents/file.txt")
        
        5. cut_to_clipboard
           - Cuts (moves) a file or folder path.
           - Input: "path" (str).
           - Example: cut_to_clipboard("C:/Users/Username/Documents/file.txt")
        
        6. paste_from_clipboard
           - Pastes a copied/cut file or folder into a target folder.
           - Input: "dest_folder" (str).
           - Example: paste_from_clipboard("C:/Users/Username/Desktop")
        
        7. delete_content
           - Moves a file or folder to the Recycle Bin.
           - Input: "path" (str).
           - Example: delete_content("C:/Users/Username/Documents/old_file.txt")
        
        8. read_file
           - Reads a file's content(UTF-8, ignore binary errors).
           - Input: "file_path" (str).
           - Example: read_file("C:/Users/Username/Documents/info.txt")
        
        9. create_item
           - Creates a new file or folder.
           - Inputs(dict):
               - "path" (str): The base path where to create the item.
               - "name" (str): The name of the new file or folder (e.g., 'notes.txt', 'NewFolder').
               - "item_type" (str): "file" or "folder".
           - Examples:
               - create_item({'{"path":"C:/Users/Username/Desktop", "name":"TestFolder", "item_type":"folder"}'})
               - create_item({'{"path":"C:/Users/Username/Desktop/TestFolder", "name":"notes.txt", "item_type":"file"}'})
        
        ---
        
        TOOL USAGE RULES:
        - Always provide exact parameter names.
        - scroll_page inputs MUST always be a dictionary with keys: steps, step_height, pause, direction.
        - Use open_folder for folders, open_file for files.
        - Use copy_to_clipboard/cut_to_clipboard for copying/moving items.
        - Use paste_from_clipboard to paste.
        - Use delete_content for deletions.
        - Use read_file to preview or summarize file content.
        - Use create_item when user requests to create a file or folder.
        - Check CURRENT PATH, AVAILABLE FILES, and SHORTCUTS before choosing a tool.
        - Never guess or invent paths.
        - There a file/folder in both "COMMON SHORTCUT PATHS" and "AVAILABLE FOLDERS AND FILES" use "AVAILABLE FOLDERS AND FILES"
        - If File name extention is not mentioned for create then create .txt file
        
        ---
        
        SMART ACTION EXAMPLES:
        
        User: "Go to Downloads"
        → open_folder("C:/Users/Username/Downloads")
        
        User: "Scroll up a bit"
        → scroll_page({{"steps": 2, "step_height": 300, "pause": 0.3, "direction": "up"}})
        
        User: "Copy this file"
        → copy_to_clipboard("C:/Users/Username/Documents/file.txt")
        
        User: "Paste it to Desktop"
        → paste_from_clipboard("C:/Users/Username/Desktop")
        
        User: "Delete old backup"
        → delete_content("C:/Users/Username/Documents/backup.zip")
        
        User: "What's in notes"
        → If notes is a file → read_file("C:/Users/Username/Documents/notes.txt")
          If notes is a folder → open_folder("C:/Users/Username/Documents/notes")
        
        User: "Create a folder named Projects"
        → create_item("C:/Users/Username/Desktop", "Projects", "folder")
        
        User: "Create an empty todo.txt in Documents"
        → If Current folder is "C:/Users/Username/Documents"
          create_item({'{"path":"C:/Users/Username/Documents", "name":"todo.txt", "item_type":"file"}'})
        
        ---
        
        BEHAVIOR GUIDELINES:
        - Always choose the most relevant tool.
        - Respond concisely and only with actions.
        - Do not describe reasoning or steps.
        - Ask for clarification ONLY if user intent is unclear or path is ambiguous.
        - NEVER hallucinate or invent actions.
        - Ask for clarification when duplicate file/folder names exist, unless already specified.
        
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
