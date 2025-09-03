from typing import List
from langchain.agents import Tool
import time
import asyncio
from src.services.selenium_service import seleniumservice

class ChromeTabToolFactory:
    def __init__(self): 
        pass

    def switch_tab(self, tab_index: int):  
        try:
            tabs = seleniumservice.chrome_driver().window_handles
            if 0 <= tab_index < len(tabs):
                seleniumservice.chrome_driver().switch_to.window(tabs[tab_index])
                return f"Chrome has switched to tab no: {tab_index+1}"
            else:
                return f"Error: Tab index {tab_index} out of range (0-{len(tabs)-1})"
        except Exception as e:
            return f"Error Occurs: {e}"  

    def new_tab(self, url: str):  
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            seleniumservice.chrome_driver().execute_script(f"window.open('{url}', '_blank');")
            tabs = seleniumservice.chrome_driver().window_handles
            seleniumservice.chrome_driver().switch_to.window(tabs[-1])
            
            return f"New tab opened with URL: {url}"
        except Exception as e: 
            return f"Error occurs: {e}"

    def close_tab(self, tab_index: int):  
        return_msg = ""
        try:
            tabs = seleniumservice.chrome_driver().window_handles
            num_tabs = len(tabs)
            
            if num_tabs == 1:
                return_msg += "Only one tab open, opening a new tab before closing. "
                seleniumservice.chrome_driver().execute_script(
                    "window.open('https://www.google.com', '_blank');"
                )
                time.sleep(1)
                tabs = seleniumservice.chrome_driver().window_handles
                num_tabs = len(tabs)
    
            if 0 <= tab_index < num_tabs:
                seleniumservice.chrome_driver().switch_to.window(tabs[tab_index])
                title = seleniumservice.chrome_driver().title
                return_msg += f"Closing Tab {tab_index} ({title}). "
                seleniumservice.chrome_driver().close()
                
                remaining_tabs = seleniumservice.chrome_driver().window_handles
                if remaining_tabs:
                    seleniumservice.chrome_driver().switch_to.window(remaining_tabs[0])
                    new_title = seleniumservice.chrome_driver().title
                    return_msg += f"Switched to Tab 0 ({new_title})"
            else:
                return_msg += f"Invalid tab index {tab_index}! Available tabs: 0-{num_tabs-1}"
                
        except Exception as e:
            return f"Error Occurs: {e}"
        
        return return_msg

    def create_tools(self) -> List[Tool]: 
        """Create tools for the agent system"""
        
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
                url = query.strip()
                return self.new_tab(url)
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
                Switch to a specific Chrome tab by index.
                Input: Tab index (0-based integer)
                Example: "2" to switch to the 3rd tab
                
                Use this when you need to switch between open browser tabs.
                Call list_chrome_tabs first to see available tabs if unsure.
                """,
            ),
            Tool(
                name="new_tab",
                func=new_tab_wrapper,
                description="""
                Open a new Chrome tab with the specified URL.
                
                Input: URL string (protocol optional, will add https:// if missing)
                Examples: 
                - "google.com"
                - "https://www.github.com"
                - "stackoverflow.com/questions/python"
                
                Use this when you need to open a new website in a new tab.
                The new tab will automatically become the active tab.
                """,
            ),
            Tool(
                name="close_tab",
                func=close_tab_wrapper,
                description="""
                Close a specific Chrome tab by index.
                
                Input: Tab index (0-based integer)
                Example: "1" to close the 2nd tab
                
                Use this when you need to close a specific browser tab.
                If only one tab is open, a new Google tab will be opened first.
                After closing, focus switches to the first remaining tab.
                Call list_chrome_tabs first to see available tabs if unsure.
                """,
            ),
        ]


_chrome_tab_factory = ChromeTabToolFactory()
chrome_tab_tools = _chrome_tab_factory.create_tools()  