from langchain_core.messages import SystemMessage, HumanMessage
from .base_edge import BaseEdge
from src.config.settings import settings


class FileManagerRedirectorEdge(BaseEdge):
    def __init__(self):
        super().__init__()

    async def execute(self, state):
        """Edge that routes to chatbot or a specific File Manager node."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query, state)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

        try:
            response = await self.llm_service.ainvoke(messages, use_pro=True)
            result = response.content.strip().lower()

            valid_nodes = {
                "chatbot",
                "filemanager_close_node",
                "filemanager_tab_node",
                "filemanager_read_node",
                "filemanager_write_node",
            }
            print(result)
            if result in valid_nodes:
                return result

            return "chatbot"

        except Exception as e:
            print(f"Router error: {e}, defaulting to 'chatbot'")
            return "chatbot"

    def get_system_message(self) -> str:
        return """
    You are a path selector (router) for the assistant. Your goal is to choose the correct path based on the user's request.
    
    Available paths:
    1. **chatbot** - only when current mode is normal or when File Manager mode is exited.
    2. **filemanager_close_node** - if user wants to close a File Manager window.
    3. **filemanager_tab_node** - if user wants modifications related to File Manager tab (opening, closing, switching windows, or opening a new folder in a new tab).
    4. **filemanager_read_node** - if user wants to VIEW, BROWSE, or READ content without modifying files.
    5. **filemanager_write_node** - if user wants to CREATE, DELETE, COPY, MOVE, or MODIFY files/folders.
    
    READ OPERATIONS (filemanager_read_node):
    - Open/browse folders in current tab
    - Open files for viewing
    - Scroll through file listings
    - Read file contents
    - View folder contents
    - Navigate within current window
    
    Examples for READ:
    - "Open the Documents folder"
    - "Scroll down to see more files" 
    - "What's in this folder?"
    - "Show me the contents of notes.txt"
    - "Go to parent folder"
    - "Navigate to Downloads"
    
    WRITE OPERATIONS (filemanager_write_node):
    - Create files or folders
    - Delete files or folders
    - Copy files or folders
    - Cut/move files or folders
    - Paste operations
    - Any modification to file system
    
    Examples for WRITE:
    - "Create a new folder called Projects"
    - "Delete this old file"
    - "Copy main.py to Desktop"
    - "Move these files to Downloads"
    - "Create a file named todo.txt"
    - "Cut this folder and paste it elsewhere"
    
    TAB OPERATIONS (filemanager_tab_node):
    - Open new tabs
    - Close tabs
    - Switch between tabs
    - Open folder in NEW tab/window
    
    Examples for TAB:
    - "Open Downloads in a new tab"
    - "Close this tab"
    - "Switch to the Pictures tab"
    - "Open new window"
    
    WINDOW OPERATIONS (filemanager_close_node):
    - Close entire File Manager window
    - Exit File Manager completely
    
    Examples for CLOSE:
    - "Close the window"
    - "Exit File Manager"
    - "Close File Manager"
    
    ROUTING DECISION LOGIC:
    1. If mentions "tab", "new tab", "switch tab" → **filemanager_tab_node**
    2. If mentions "close window", "exit" → **filemanager_close_node**  
    3. If mentions create, delete, copy, cut, paste, move → **filemanager_write_node**
    4. If mentions open folder, scroll, read, view, browse, navigate → **filemanager_read_node**
    5. If current mode is normal or File Manager exited → **chatbot**
    
    IMPORTANT NOTES:
    - "Open folder" in current window = **filemanager_read_node**
    - "Open folder in new tab" = **filemanager_tab_node**
    - Don't go to filemanager_close_node unless user explicitly wants to close window
    - One window can have multiple tabs
    - Return only the node name in lowercase
    """

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""

    def _format_human_message(self, messages, user_query, state):
        return f"""
    Conversation so far:
    {self.formatter_without_tools(messages)}
    Latest user message:
    {user_query}
    Current Mode: {settings.mode}
    Please select the correct path: "chatbot","filemanager_close_node","filemanager_tab_node","filemanager_read_node","filemanager_write_node".
    """
