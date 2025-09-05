from typing import List
from langchain.agents import Tool
import time
import asyncio
from src.services.selenium_service import seleniumservice

class FileManagerTabToolFactory:
    def __init__(self): 
        pass

    def switch_tab(self, tab_index: int):  
        try:
            tabs = seleniumservice.chrome_driver(files_mode=True).window_handles
            if 0 <= tab_index < len(tabs):
                seleniumservice.chrome_driver(files_mode=True).switch_to.window(tabs[tab_index])
                return f"File Manager has switched to tab no: {tab_index+1}"
            else:
                return f"Error: tab index {tab_index} out of range (0-{len(tabs)-1})"
        except Exception as e:
            return f"Error Occurs: {e}"  

    def new_tab(self, path: str):  
        try:
            # Treat path as a direct file path without adding http:// or https://
            formatted_path = f'file:///{path.replace("\\\\", "/").replace("\\", "/")}'
            seleniumservice.chrome_driver(files_mode=True).execute_script(f"window.open('{formatted_path}', '_blank');")
            tabs = seleniumservice.chrome_driver(files_mode=True).window_handles
            seleniumservice.chrome_driver(files_mode=True).switch_to.window(tabs[-1])
            
            return f"New File Manager tab opened at: {path}"
        except Exception as e: 
            return f"Error occurs: {e}"

    def close_tab(self, tab_index: int):  
        return_msg = ""
        try:
            tabs = seleniumservice.chrome_driver(files_mode=True).window_handles
            num_tabs = len(tabs)
            
            if num_tabs == 1:
                return_msg += "Only one tab open, opening a new blank tab before closing. "
                seleniumservice.chrome_driver(files_mode=True).execute_script(
                    "window.open('file:///C:/Users/', '_blank');"
                )
                tabs = seleniumservice.chrome_driver(files_mode=True).window_handles
                num_tabs = len(tabs)
    
            if 0 <= tab_index < num_tabs:
                seleniumservice.chrome_driver(files_mode=True).switch_to.window(tabs[tab_index])
                title = seleniumservice.chrome_driver(files_mode=True).title
                return_msg += f"Closing tab {tab_index} ({title}). "
                seleniumservice.chrome_driver(files_mode=True).close()
                
            else:
                return_msg += f"Invalid tab index {tab_index}! Available tabs: 0-{num_tabs-1}"
                
        except Exception as e:
            return f"Error Occurs: {e}"
        
        return return_msg

    def create_tools(self) -> List[Tool]: 
        """Create tools for File Manager mode"""
        
        def switch_tab_wrapper(query):
            try:
                tab_index = int(query.strip())
                return self.switch_tab(tab_index)
            except ValueError:
                return f"Error: '{query}' is not a valid tab index. Please provide an integer."
            except Exception as e:
                return f"Error in switch_tab_wrapper: {e}"
        
        def new_tab_wrapper(query):
            try:
                path = query.strip()
                return self.new_tab(path)
            except Exception as e:
                return f"Error in new_tab_wrapper: {e}"
        
        def close_tab_wrapper(query):
            try:
                tab_index = int(query.strip())
                return self.close_tab(tab_index)
            except ValueError:
                return f"Error: '{query}' is not a valid tab index. Please provide an integer."
            except Exception as e:
                return f"Error in close_tab_wrapper: {e}"
        
        return [
            Tool(
                name="switch_tab",
                func=switch_tab_wrapper,
                description="""
                Switch to a specific File Manager tab by index.
                Input: tab index (0-based integer)
                Example: "2" to switch to the 3rd File Manager tab.
                
                Use this when you need to switch between open File Manager tabs.
                """,
            ),
            Tool(
                name="new_tab",
                func=new_tab_wrapper,
                description="""
                Open a new File Manager tab at a specified path.

                IMPORTANT: Do NOT add 'http://' or 'https://' to the path.
                Input: Full folder path string (absolute path only)
                Examples:
                - "C:\\Users\\bhanu\\Documents"
                - "C:\\Users\\bhanu\\Desktop"

                Use this to open a folder directly in a new File Manager tab.
                """,
            ),
            Tool(
                name="close_tab",
                func=close_tab_wrapper,
                description="""
                Close a specific File Manager tab by index.
                
                Input: tab index (0-based integer)
                Example: "1" to close the 2nd File Manager tab.
                
                If only one tab is open, a new blank one will be opened first.
                After closing, focus switches to the first remaining tab.
                """,
            ),
        ]


_file_manager_tab_factory = FileManagerTabToolFactory()
file_manager_tab_tools = _file_manager_tab_factory.create_tools()
