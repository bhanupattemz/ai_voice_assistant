import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_node import BaseNode
from src.config.settings import settings
from src.core.state import AssistantState
from src.tools.softwares_tool import software_tools


class SoftwareNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        """Node that decides whether to use a Software tool."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = await self.llm_service.abind_tools(software_tools)
        response = await llm.ainvoke(messages)
        return {"messages": [response]}

    def get_system_message(self) -> str:
        return f"""You are {settings.assistant_name}, a Windows AI assistant specializing in software management.
Current time: {self._get_current_time()}

ROLE: Software Management Specialist
GOAL: Execute software-related tasks using appropriate tools

AVAILABLE TOOLS:
1. open_app(app_name): Launch applications
2. check_software(app_name): Verify if apps are installed  
3. check_harmful_software(query): Scan for malicious software

TOOL SELECTION RULES:
- Launch requests → open_app()
- Installation checks → check_software()  
- Security concerns → check_harmful_software()

EXECUTION STRATEGY:
1. Identify user intent from request
2. Extract application name or security context
3. Call appropriate tool immediately
4. Provide clear status response

APP NAME PROCESSING:
- Accept partial names: "chrome" → "Google Chrome"
- Handle abbreviations: "calc" → "Calculator"
- Case-insensitive matching
- Smart fuzzy matching for variations

RESPONSE FORMAT:
- Success: "✅ [Action completed]: [Details]"
- Failure: "❌ [Issue]: [Reason]"
- Security: Detailed threat analysis with recommendations

Execute tool calls immediately upon request identification."""

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""TASK: Analyze user request and execute appropriate software tool

USER REQUEST: "{user_query}"

DECISION MATRIX:
Launch Intent → open_app(app_name)
- Keywords: open, launch, start, run, execute, boot
- Examples: "open chrome", "start calculator", "run notepad"

Check Intent → check_software(app_name)  
- Keywords: check, installed, available, have, exists, present
- Examples: "is firefox installed", "do I have photoshop", "check steam"

Security Intent → check_harmful_software(query)
- Keywords: virus, malware, harmful, scan, security, threat
- Examples: "scan for malware", "check viruses", "security audit"

EXECUTION RULES:
1. Extract app name from request (ignore articles like "the", "a")
2. Choose single most appropriate tool based on primary intent
3. Call tool immediately with extracted parameters
4. Do not explain what you will do - just execute

PARAMETER EXTRACTION:
- App names: Extract core application identifier
- Security queries: Use full context or empty string for general scan

EXECUTE NOW."""
