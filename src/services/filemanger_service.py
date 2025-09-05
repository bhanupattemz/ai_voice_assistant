import ctypes
import string
import os
import winshell


class FileManagerService:
    def __init__(self):
        pass

    def get_system_drives(self):
        drives = []
        bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1
        return drives

    def is_safe(self, path):

        path = os.path.abspath(path)
        drive = os.path.splitdrive(path)[0].upper()
        if drive != "C:":
            return True
        user_profile = os.environ.get("USERPROFILE", r"C:\Users\Default")

        safe_folders = [
            os.path.join(user_profile, "Desktop"),
            os.path.join(user_profile, "Documents"),
            os.path.join(user_profile, "Downloads"),
            os.path.join(user_profile, "Pictures"),
            os.path.join(user_profile, "Videos"),
            os.path.join(user_profile, "Music"),
            os.path.join(user_profile, "AppData", "Local", "Temp"),
            os.path.join(user_profile, "OneDrive", "Desktop"),
            os.path.join(user_profile, "OneDrive", "Documents"),
            os.path.join(user_profile, "OneDrive", "Pictures"),
            os.path.join(user_profile, "OneDrive", "Videos"),
            os.path.join(user_profile, "OneDrive", "Downloads"),
            os.path.join(user_profile, "OneDrive", "Music"),
        ]
        for folder in safe_folders:
            folder = os.path.abspath(folder)
            if path.startswith(folder):
                return True

        return False

    def get_common_windows_paths(self):
        user_profile = os.environ.get("USERPROFILE", r"C:\Users\Default")
        one_drive = os.environ.get("OneDrive", os.path.join(user_profile, "OneDrive"))
        public = os.path.join(os.environ.get("PUBLIC", r"C:\Users\Public"))

        paths = {
            "Desktop|Desk": os.path.join(user_profile, "Desktop"),
            "Documents|Docs|Doc": os.path.join(user_profile, "Documents"),
            "Downloads|Download": os.path.join(user_profile, "Downloads"),
            "Pictures|Photos|Images|Pics": os.path.join(user_profile, "Pictures"),
            "Videos|Movies|Clips": os.path.join(user_profile, "Videos"),
            "Music|Songs|Audio": os.path.join(user_profile, "Music"),
            "OneDrive": one_drive,
            "Temp|Temporary": os.environ.get(
                "TEMP", os.path.join(user_profile, "AppData", "Local", "Temp")
            ),
            "Favorites|Bookmarks": os.path.join(user_profile, "Favorites"),
            "Links|Shortcuts": os.path.join(user_profile, "Links"),
            "Saved Games|Games": os.path.join(user_profile, "Saved Games"),
            "Contacts|People": os.path.join(user_profile, "Contacts"),
            "Public Desktop": os.path.join(public, "Desktop"),
            "Public Documents": os.path.join(public, "Documents"),
            "Public Pictures": os.path.join(public, "Pictures"),
            "Public Videos": os.path.join(public, "Videos"),
            "Recycle Bin|Trash": winshell.recycle_bin(),
        }

        result = ",\n".join([f"{aliases} : {path}" for aliases, path in paths.items()])
        return result

    def get_folder_contents(self, folder_path):
        try:
            entries = os.listdir(folder_path)
            folders = [
                entry
                for entry in entries
                if os.path.isdir(os.path.join(folder_path, entry))
            ]
            files = [
                entry
                for entry in entries
                if os.path.isfile(os.path.join(folder_path, entry))
            ]    

            result = "Folders:\n"
            result += "\n".join(folders) if folders else "None"
            result += "\n\nFiles:\n"
            result += "\n".join(files) if files else "None"    

            return result
        except FileNotFoundError:
            return f"The folder '{folder_path}' does not exist."
        except PermissionError:
            return f"Permission denied to access '{folder_path}'."
        return None
