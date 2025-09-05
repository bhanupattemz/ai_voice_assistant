import time
import os
import platform
import win32clipboard
from win32com.shell import shell, shellcon
from send2trash import send2trash
import shutil
from typing import List
from langchain.agents import Tool
from src.services.selenium_service import seleniumservice
from src.services.filemanger_service import FileManagerService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FileManagerFuncToolFactory:
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

    def copy_to_clipboard(self, path: str):
        if not os.path.exists(path):
            return f"Invalid path: {path}"
        if not self.filemanager_services.is_safe(path=path):
            return f"{path} is restricted"

        abs_path = os.path.abspath(path)
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(f"copy,{abs_path}")
        win32clipboard.CloseClipboard()
        return f"'{path}' copied to clipboard."

    def cut_to_clipboard(self, path: str):
        if not os.path.exists(path):
            return f"Invalid path: {path}"
        if not self.filemanager_services.is_safe(path=path):
            return f"{path} is restricted"

        abs_path = os.path.abspath(path)
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(f"cut,{abs_path}")
        win32clipboard.CloseClipboard()
        return f"'{path}' cut to clipboard."

    def paste_from_clipboard(self, dest_folder: str):
        if not os.path.isdir(dest_folder):
            return f"Invalid destination folder: {dest_folder}"
        if not self.filemanager_services.is_safe(path=dest_folder):
            return f"{dest_folder} is restricted"
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData()
        except:
            win32clipboard.CloseClipboard()
            return "Clipboard is empty or invalid."
        finally:
            win32clipboard.CloseClipboard()
        if not data or "," not in data:
            return "Clipboard does not contain a valid file path."

        operation, src_path = data.split(",", 1)
        if not self.filemanager_services.is_safe(path=src_path):
            return f"{src_path} is restricted"
        src_path = os.path.abspath(src_path)
        if not os.path.exists(src_path):
            return f"Source path does not exist: {src_path}"
        base_name = os.path.basename(src_path)
        dest_path = os.path.join(dest_folder, base_name)

        try:
            if os.path.isdir(src_path):
                if operation == "copy":
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.move(src_path, dest_path)
            else:
                if operation == "copy":
                    shutil.copy2(src_path, dest_path)
                else:
                    shutil.move(src_path, dest_path)
        except Exception as e:
            return f"Error during paste: {e}"

        return f"Pasted '{src_path}' to '{dest_folder}' using {operation} operation."

    def delete_content(self, path: str):
        if not os.path.exists(path):
            return f"Path does not exist: {path}"

        if not self.filemanager_services.is_safe(path=path):
            return f"{path} is restricted"

        try:
            send2trash(path)
            return f"'{path}' moved to Recycle Bin."
        except Exception as e:
            return f"Error moving '{path}' to Recycle Bin: {e}"

    def read_file(self, file_path: str):
        if not os.path.isfile(file_path):
            print(f"Invalid file path: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "rb") as f:
                return f.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

    def create_item(self, data:dict) -> str:
        full_path = os.path.join(path, name)
        path=data.get("path",None)
        name=data.get("name",None)
        item_type=data.get("item_type",None)
        if not (path and name and item_type):
            return "path or name or item_type is missing"
        try:
            if item_type.lower() == "folder":
                os.makedirs(full_path, exist_ok=True)
                return f"Folder created: {full_path}"

            elif item_type.lower() == "file":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write("")
                return f"File created: {full_path}"

            else:
                return "Invalid item_type. Use 'file' or 'folder'."

        except Exception as e:
            return f"Error creating item: {e}"

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
                name="copy_to_clipboard",
                func=self.copy_to_clipboard,
                description="""
                Copies a file or folder path to clipboard.
                
                Input: 
                "path" (str): Full path to the file or folder.
                
                Output: Confirmation message.
                """,
            ),
            Tool(
                name="cut_to_clipboard",
                func=self.cut_to_clipboard,
                description="""
                Cuts (moves) a file or folder path to clipboard.
                
                Input: 
                "path" (str): Full path to the file or folder.
                
                Output: Confirmation message.
                """,
            ),
            Tool(
                name="paste_from_clipboard",
                func=self.paste_from_clipboard,
                description="""
                Pastes the previously copied or cut item into a destination folder.
                
                Input: 
                "dest_folder" (str): Full path of the destination folder.
                
                Output: Success or error message.
                """,
            ),
            Tool(
                name="delete_content",
                func=self.delete_content,
                description="""
                Moves a file or folder to the Recycle Bin.
                
                Input: 
                "path" (str): Full path to the file or folder.
                
                Output: Success or error message.
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
            Tool(
                name="create_item",
                func=self.create_item,
                description="""
                Create a file or folder at the specified path.    
        
                Args(dict):
                    path (str): Base directory where the file/folder should be created.
                    name (str): Name of the file or folder (e.g., 'abc.txt' or 'NewFolder').
                    item_type (str): 'file' or 'folder'.    
        
                Returns:
                    str: Message with the status of the operation.
                """,
            ),
        ]


_filemanager_func_factory = FileManagerFuncToolFactory()
filemanager_func_tools = _filemanager_func_factory.create_tools()
