from typing import List
from langchain.agents import Tool
from src.config.settings import settings
import os
import platform
import subprocess
import json
import winreg
from src.services.llm_service import LLMService
from pydantic import BaseModel, Field


class TargetOutput(BaseModel):
    app_name: str = Field(description="The exact application name found in the system that best matches the user's request")
    have_app: bool = Field(description="True if the requested application is available in the system, False otherwise")


class HarmfullSoftwaresOutput(BaseModel):
    more_harmfull: List[str] = Field(description="List of applications that are potentially more harmful or suspicious")
    less_harmfull: List[str] = Field(description="List of applications that may have minor security concerns but are generally safe")
    have_apps: bool = Field(description="True if any potentially harmful applications were found, False if none detected")


class SoftwareToolFactory:
    def __init__(self):
        self.llm = LLMService().llm.with_structured_output(TargetOutput)
        self.llm_for_harmfull = LLMService().llm.with_structured_output(HarmfullSoftwaresOutput)
        system = platform.system()
        if system != "Windows":
            print("⚠ This function only works on Windows.")
            return
        start_menu_paths = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        self.apps = {}
        for path in start_menu_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(".lnk"):
                            app_name = os.path.splitext(file)[0]
                            self.apps[app_name] = os.path.join(root, file)
        self._add_system_apps()
        
        self._add_store_apps()

    def _add_system_apps(self):
        """Add common Windows system applications"""
        system_apps = {
            'Calculator': 'calc.exe',
            'Notepad': 'notepad.exe', 
            'Paint': 'mspaint.exe',
            'Command Prompt': 'cmd.exe',
            'PowerShell': 'powershell.exe',
            'Registry Editor': 'regedit.exe',
            'Task Manager': 'taskmgr.exe',
            'Control Panel': 'control.exe',
            'File Explorer': 'explorer.exe',
            'System Information': 'msinfo32.exe',
            'Character Map': 'charmap.exe',
            'Disk Cleanup': 'cleanmgr.exe',
            'Device Manager': 'devmgmt.msc',
            'Disk Management': 'diskmgmt.msc',
            'Event Viewer': 'eventvwr.msc',
            'Services': 'services.msc',
            'Computer Management': 'compmgmt.msc',
            'System Configuration': 'msconfig.exe',
            'Resource Monitor': 'resmon.exe',
            'Performance Monitor': 'perfmon.exe',
            'Windows Memory Diagnostic': 'mdsched.exe',
            'Windows Settings': 'ms-settings:',
            'Microsoft Store': 'ms-windows-store:',
            'Windows Security': 'windowsdefender:',
            'Magnifier': 'magnify.exe',
            'On-Screen Keyboard': 'osk.exe',
            'Narrator': 'narrator.exe',
            'Sound Recorder': 'soundrecorder.exe',
            'Steps Recorder': 'psr.exe',
            'Snipping Tool': 'snippingtool.exe',
            'Windows Media Player': 'wmplayer.exe',
        }
        
        for name, executable in system_apps.items():
            if name not in self.apps:
                self.apps[name] = executable

    def _add_store_apps(self):
        """Add Microsoft Store apps using PowerShell"""
        try:
            cmd = [
                'powershell', '-Command',
                'Get-StartApps | Where-Object {$_.AppID -like "*!*"} | Select-Object Name, AppID | ConvertTo-Json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=True)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    store_apps = json.loads(result.stdout)
                    if isinstance(store_apps, dict):
                        store_apps = [store_apps]
                    
                    for app_data in store_apps:
                        if isinstance(app_data, dict) and 'Name' in app_data and 'AppID' in app_data:
                            app_name = app_data['Name']
                            app_id = app_data['AppID']
                            if app_name and app_name not in self.apps:
                                self.apps[app_name] = app_id
                            
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        
        common_store_apps = {
            'Microsoft Edge': 'msedge.exe',
            'Photos': 'ms-photos:',
            'Camera': 'microsoft.windowscamera:',
            'Movies & TV': 'mswindowsvideo:',
            'Groove Music': 'mswindowsmusic:',
            'Mail': 'outlookmail:',
            'Calendar': 'outlookcal:',
            'Maps': 'bingmaps:',
            'Weather': 'msnweather:',
            'News': 'bingnews:',
            'Microsoft Teams': 'msteams:',
            'Xbox': 'ms-xbl-3d8b930f:',
            'Microsoft To Do': 'ms-todo:',
            'Sticky Notes': 'ms-stickynotes:',
            'Voice Recorder': 'ms-callrecording:',
            'Clock': 'ms-clock:',
            'LinkedIn': 'LinkedIn',  
        }
        
        for name, protocol in common_store_apps.items():
            if name not in self.apps:
                self.apps[name] = protocol

    def check_app(self, app_name: str):
        """Check if an application exists in the system"""
        if not self.apps:
            return "No applications found or system not supported"
            
        app_list = "\n".join([f"- {name}" for name in self.apps.keys()])
        
        prompt = f"""TASK: Match user request with installed application

AVAILABLE APPLICATIONS:
{app_list}

USER REQUEST: "{app_name}"

MATCHING RULES:
1. Find exact or best partial match
2. Handle abbreviations and common names
3. Case-insensitive matching
4. Set have_app=True only for reasonable matches

COMMON MAPPINGS:
- chrome/google → Google Chrome
- word/msword → Microsoft Word  
- calc/calculator → Calculator
- notepad/text → Notepad
- cmd/command → Command Prompt
- edge/browser → Microsoft Edge
- store/ms store → Microsoft Store
- settings/control → Windows Settings
- camera/cam → Camera
- linkedin/linked → LinkedIn
- explorer/filemanager/files → File Explorer

STRICT MATCHING:
- DO NOT match unrelated apps (e.g., camera should NOT match File Explorer)
- Only return have_app=True if there's a reasonable semantic match
- Be specific with application names

OUTPUT REQUIREMENTS:
- app_name: Exact name from available list
- have_app: True if confident match found

Match the request to available applications now."""
        
        try:
            result = self.llm.invoke(prompt)
            if result.have_app:
                return f"Found: {result.app_name}"
            else:
                return f"Application '{app_name}' not found in system"
        except Exception as e:
            return f"Error checking application: {str(e)}"

    def open_app(self, app_name: str):
        """Opens an application by name if found in Start Menu"""
        if not self.apps:
            return "No applications found or system not supported"
            
        app_list = "\n".join([f"- {name}" for name in self.apps.keys()])
        
        prompt = f"""TASK: Match user request with installed application for launching

AVAILABLE APPLICATIONS:
{app_list}

USER REQUEST: "{app_name}"

MATCHING RULES:
1. Find exact or best partial match
2. Handle abbreviations and common names
3. Case-insensitive matching
4. Set have_app=True only for reasonable matches

COMMON MAPPINGS:
- chrome/google → Google Chrome
- word/msword → Microsoft Word  
- calc/calculator → Calculator
- notepad/text → Notepad
- cmd/command → Command Prompt
- firefox/ff → Firefox
- steam/game → Steam
- discord/chat → Discord
- edge/browser → Microsoft Edge
- store/ms store → Microsoft Store
- settings/control → Windows Settings
- camera/cam → Camera
- linkedin/linked → LinkedIn
- explorer/filemanager/files → File Explorer

STRICT MATCHING:
- DO NOT match unrelated apps (e.g., camera should NOT match File Explorer)
- Only return have_app=True if there's a reasonable semantic match
- Be specific with application names

OUTPUT REQUIREMENTS:
- app_name: Exact name from available list
- have_app: True if confident match found

Match the request to available applications for launching."""
        
        try:
            result = self.llm.invoke(prompt)
            if not result.have_app:
                return f"Application '{app_name}' not found in system"

            if result.app_name in self.apps:
                try:
                    app_path = self.apps[result.app_name]
                    
                    if app_path.startswith('ms-') or app_path.endswith(':'):
                        subprocess.Popen(["start", "", app_path], shell=True)
                    elif '!' in app_path:
                        subprocess.Popen(["explorer", f"shell:AppsFolder\\{app_path}"], shell=True)
                    elif app_path.startswith('shell:AppsFolder'):
                        subprocess.Popen(["explorer", app_path], shell=True)
                    elif app_path.endswith('.exe') or app_path.endswith('.msc'):
                        subprocess.Popen([app_path], shell=True)
                    else:
                        subprocess.Popen(["start", "", app_path], shell=True)
                    
                    return f"Successfully opened {result.app_name}"
                except Exception as e:
                    return f"Failed to open {result.app_name}: {str(e)}"
            else:
                return f"Application path not found for {result.app_name}"
                
        except Exception as e:
            return f"Error opening application: {str(e)}"

    def check_harmfull(self, query: str = ""):
        """Analyze installed applications for potential security concerns"""
        if not self.apps:
            return HarmfullSoftwaresOutput(more_harmfull=[], less_harmfull=[], have_apps=False)
            
        app_list = "\n".join([f"- {name}" for name in self.apps.keys()])
        
        prompt = f"""TASK: Security analysis of installed applications

INSTALLED APPLICATIONS:
{app_list}

ANALYSIS CONTEXT: {query if query else 'General security scan'}

CLASSIFICATION CRITERIA:

HIGH RISK (more_harmfull):
- Known malware signatures
- Cryptocurrency miners
- Keyloggers and spyware
- Remote access trojans
- Browser hijackers
- Cracked software with potential backdoors
- Suspicious unknown executables

LOW RISK (less_harmfull):  
- Legitimate apps with privacy concerns
- Outdated software versions
- Potentially unwanted programs (PUPs)
- Aggressive advertising software
- System optimizers with questionable practices

ANALYSIS RULES:
1. Only flag applications with genuine security concerns
2. Distinguish between legitimate and suspicious software
3. Include only application names in output lists
4. Set have_apps=True if ANY threats found
5. Prioritize actual security risks over preferences

THREAT INDICATORS:
- Unusual file locations
- Suspicious naming patterns
- Known malware families
- Applications commonly used maliciously

Perform security analysis now."""
        
        try:
            result = self.llm_for_harmfull.invoke(prompt)
            return result
        except Exception as e:
            return HarmfullSoftwaresOutput(
                more_harmfull=[f"Error analyzing applications: {str(e)}"], 
                less_harmfull=[], 
                have_apps=True
            )

    def create_tools(self) -> List[Tool]:
        """Create tools for the agent system"""
        return [
            Tool(
                name="open_app",
                func=self.open_app,
                description="""Launch applications on Windows system.

USE FOR: Opening, launching, starting, running, or executing applications
KEYWORDS: open, launch, start, run, execute, boot up
INPUT: Application name (accepts partial names, abbreviations, common names)

EXAMPLES:
- "open chrome" → launches Google Chrome
- "start calculator" → opens Calculator
- "run notepad" → opens Notepad
- "launch word" → opens Microsoft Word

The tool handles fuzzy matching and common app nicknames automatically."""
            ),
            Tool(
                name="check_software",
                func=self.check_app,
                description="""Check if specific applications are installed on the system.

USE FOR: Verifying application availability before use or installation
KEYWORDS: check, installed, available, have, exists, present, verify
INPUT: Application name to verify

EXAMPLES:
- "is photoshop installed?" → checks for Adobe Photoshop
- "do I have steam?" → verifies Steam installation  
- "check for firefox" → looks for Firefox browser

Returns confirmation of application presence or absence."""
            ),
            Tool(
                name="check_harmful_software",
                func=self.check_harmfull,
                description="""Scan installed applications for security threats and malicious software.

USE FOR: Security audits, malware detection, system safety checks
KEYWORDS: virus, malware, harmful, suspicious, security, scan, threat, audit
INPUT: Optional context string (empty for general scan)

EXAMPLES:
- "scan for malware" → comprehensive security scan
- "check for viruses" → virus detection scan
- "security audit" → full threat analysis

Returns categorized list of potential threats with risk levels."""
            ),
        ]


_software_factory = SoftwareToolFactory()
software_tools = _software_factory.create_tools()