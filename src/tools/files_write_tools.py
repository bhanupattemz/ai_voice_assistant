import os
import win32clipboard
from send2trash import send2trash
import shutil
from typing import List
from langchain.agents import Tool
from src.services.filemanger_service import FileManagerService
from langchain.tools import StructuredTool


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

    def create_file(self, data: str) -> str:
        path,name=data.split(",")
        full_path = os.path.join(path, name)
        if not (path and name):
            return "path or name is missing"

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("")
            return f"File created: {full_path}"
        except Exception as e:
            return f"Error creating item: {e}"

    def create_folder(self, data: str) -> str:
        path,name=data.split(",")
        full_path = os.path.join(path, name)
        if not (path and name):
            return "path or name is missing"
        try:
            os.makedirs(full_path, exist_ok=True)
            return f"Folder created: {full_path}"
        except Exception as e:
            return f"Error creating item: {e}"

    def create_tools(self) -> List[Tool]:
        """Create and return all File Manager tools for agent usage with detailed descriptions."""
        return [
            Tool(
                name="copy_to_clipboard",
                func=self.copy_to_clipboard,
                description="""UseFul when user want to Copy a file or folder to clipboard for later pasting.""",
            ),
            Tool(
                name="cut_to_clipboard",
                func=self.cut_to_clipboard,
                description="""UseFul when user want to Cut (move) a file or folder to clipboard for later pasting.""",
            ),
            Tool(
                name="paste_from_clipboard",
                func=self.paste_from_clipboard,
                description="""UseFul when user want to Paste previously copied or cut items from clipboard to destination folder.""",
            ),
            Tool(
                name="delete_content",
                func=self.delete_content,
                description="""UseFul when user want to Delete a file or folder by moving it to Recycle Bin.""",
            ),
            Tool(
                name="create_file",
                func=self.create_file,
                description="""UseFul when user want to Create a file at the specified path."""
            ),
            Tool(
                name="create_folder",
                description="Usefull when user want to Create a folder at the specified path",
                func=self.create_folder,
            ),
        ]


_filemanager_write_factory = FileManagerWriteToolFactory()
filemanager_write_tools = _filemanager_write_factory.create_tools()
