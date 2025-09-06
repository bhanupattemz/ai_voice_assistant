import time
import os
import platform
from typing import List
from langchain.agents import Tool
from src.services.selenium_service import seleniumservice
from src.services.filemanger_service import FileManagerService


class FileManagerReadToolFactory:
    def __init__(self):
        self.filemanager_services = FileManagerService()

    def scroll_page(self, steps):
        step_height = steps.get("step_height", 500)
        pause = steps.get("pause", 0.3)
        direction = steps.get("direction", "down")
        steps = int(steps.get("steps", 1))

        driver = seleniumservice.chrome_driver()
        if direction.lower() == "up":
            step_height = -abs(step_height)
        else:
            step_height = abs(step_height)

        for _ in range(steps):
            driver.execute_script(f"window.scrollBy(0, {step_height});")
            time.sleep(pause)

        return f"Scrolled {steps} steps {direction} by {abs(step_height)}px each"

    def open_folder(self, path: str):

        driver = seleniumservice.chrome_driver()
        driver.implicitly_wait(10)
        try:
            driver.get(f"file:///{path}")
            return f"Opened folder '{path}' successfully"
        except Exception as e:
            return f"Error Occurred: {e}"

    def open_file(self, file_path: str):
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(file_path)

            return f"Opened file: {file_path}"
        except Exception as e:
            return f"Failed to open {file_path}: {e}"

    def read_file(self, file_path: str):
        if not os.path.isfile(file_path):
            return f"Invalid file path: {file_path}"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "rb") as f:
                return f.read().decode("utf-8", errors="ignore")
        except Exception as e:
            return f"Error reading file: {e}"

    def create_tools(self) -> List[Tool]:
        """Create and return all File Manager tools for agent usage with detailed descriptions."""
        return [
            Tool(
                name="scroll_page",
                func=self.scroll_page,
                description="""
                Scrolls through a File Manager window (simulated in a browser view).
                
                Input (dict):
                {
                  "steps": int,           # Number of scroll steps
                  "step_height": int,     # Pixels per step (default: 500)
                  "pause": float,         # Pause between steps in seconds (default: 0.3)
                  "direction": str        # "up" or "down" (default: "down")
                }
                
                Example:
                {"steps": 3, "step_height": 400, "direction": "down"}
                
                Output: Confirmation message of scroll action.
                """,
            ),
            Tool(
                name="open_folder",
                func=self.open_folder,
                description="""
                Opens a folder in File Manager (in a browser tab via Selenium).
                
                Input: 
                "path" (str): Full path to the folder.
                
                Example:
                open_folder("C:/Users/Username/Documents")
                
                Output: Success or error message.
                Notes: Folder will open in the current browser tab.
                """,
            ),
            Tool(
                name="open_file",
                func=self.open_file,
                description="""
                Opens a file using the system's default application.
                
                Input: 
                "file_path" (str): Full path to the file.
                
                Output: Confirmation or error message.
                """,
            ),
            Tool(
                name="read_file",
                func=self.read_file,
                description="""
                Reads the contents of a text file as a string.
                
                Input: 
                "file_path" (str): Full path to the text file.
                
                Output: String content of the file.
                Notes: Returns None for invalid or binary files.
                """,
            ),
        ]


_filemanager_read_factory = FileManagerReadToolFactory()
filemanager_read_tools = _filemanager_read_factory.create_tools()
