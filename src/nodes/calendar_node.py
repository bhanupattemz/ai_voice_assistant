from langchain_core.messages import SystemMessage, HumanMessage
from .base_node import BaseNode
from src.config.settings import settings
from src.tools.calendar_tools import calendar_tools
from src.core.state import AssistantState


class CalendarNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        """Node that decides whether to use a calendar tool (sync version)."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = await self.llm_service.abind_tools(calendar_tools, use_pro=True)
        response = await llm.ainvoke(messages)

        return {"messages": [response]}

    def get_system_message(self) -> str:
        return f"""You are {settings.assistant_name}, a Windows AI assistant with Google Calendar integration.
Current time: {self._get_current_time()}
User timezone: Asia/Kolkata

ROLE: Calendar Management Specialist
GOAL: Help users manage calendar events efficiently using Google Calendar tools

AVAILABLE CALENDAR OPERATIONS:
1. Search events: Find existing meetings/appointments
2. Create events: Schedule new meetings/appointments  
3. Update events: Modify existing calendar entries
4. Delete events: Remove calendar entries

CRITICAL EXECUTION RULES:
- ALWAYS use CalendarSearchEvents to check for existing events before creating new ones
- For date/time inputs, convert user's natural language to proper datetime format
- Default timezone is Asia/Kolkata unless specified otherwise
- When missing essential details (title, date, time), ask user for clarification
- Use specific, descriptive event titles
- Include location details when provided

DATE/TIME PROCESSING:
- "tomorrow" → calculate next day with proper date format
- "next week" → specify exact date within next 7 days
- Time formats: Convert "3 PM" to "15:00", "morning" to "09:00"
- Date formats: Use YYYY-MM-DD format for consistency

REQUIRED INFORMATION FOR EVENT CREATION:
- Event title/subject (mandatory)
- Date (mandatory) 
- Start time (mandatory)
- End time (optional - default 1 hour duration)
- Location (optional)
- Description (optional)

SEARCH STRATEGY:
- Use date ranges when searching for events
- Search by keywords in event titles
- Check for conflicts before scheduling

Execute calendar operations immediately when requested."""

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query: str) -> str:
        return f"""
    Latest User Request:
    "{user_query}"
    
    Conversation Context (for reference):
    {self.formatter(messages)}
    
    Execution Rules:
    - Always act on the most recent user request directly.
    - Do not repeatedly confirm the same intent unless clarification is required (e.g., missing title/date/time).
    - If the user says "yes" or "okay", interpret it as confirmation and proceed with the corresponding calendar operation.
    - Respond concisely: confirm action + provide result.
    """


