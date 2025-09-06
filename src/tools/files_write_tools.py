import os
import win32clipboard
from send2trash import send2trash
import shutil
from typing import List
from langchain.agents import Tool
from src.services.filemanger_service import FileManagerService


class FileManagerWriteToolFactory:
    def __init__(self):
        self.filemanager_services = FileManagerService()

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

    def create_item(self, data: dict) -> str:
        print("+++++++++", data, "++++++++++++++++", type(data))
        path = data.get("path", None)
        name = data.get("name", None)
        item_type = data.get("item_type", None)
        full_path = os.path.join(path, name)
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
                name="create_item",
                func=self.create_item,
                description="""
                Create a file or folder at the specified path.    
        
                Args(dict):
                {
                    "path" : str        # Base directory where the file/folder should be created.
                    "name" : str        # Name of the file or folder (e.g., 'abc.txt' or 'NewFolder').
                    "item_type" : str   # 'file' or 'folder'.    
                }
                Returns:
                    str: Message with the status of the operation.
                """,
            ),
        ]


_filemanager_write_factory = FileManagerWriteToolFactory()
filemanager_write_tools = _filemanager_write_factory.create_tools()
