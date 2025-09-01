from langchain_core.messages import SystemMessage, HumanMessage
from src.nodes.calendar.base_node import CalendarBaseNode
from src.config.settings import settings
from src.core.state import AssistantState
import datetime
from pydantic import BaseModel, Field


class DateOutput(BaseModel):
    start: str = Field(description="Start date in ISO format (YYYY-MM-DDTHH:MM:SS)")
    end: str = Field(description="End date in ISO format (YYYY-MM-DDTHH:MM:SS)")


class CalendarNode(CalendarBaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        
        llm = self.llm_service.llm.with_structured_output(DateOutput)
        dates = await llm.ainvoke(messages)
        
        start_date = datetime.datetime.fromisoformat(dates.start.replace('Z', ''))
        end_date = datetime.datetime.fromisoformat(dates.end.replace('Z', ''))
        
        events_data = self.get_reminders(start_date, end_date)
        
    
        return {"calendar_events": events_data}

    def get_reminders(self, start, end):
        service = self.get_calendar_service()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start.isoformat() + "Z",
                timeMax=end.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return events

    
    def get_system_message(self):
        return f"""You are a calendar date range parser.

ROLE:
- Extract the best possible start and end dates from the user's query.
- Keep enough context (e.g., a full month or week) to avoid missing events.

GUIDELINES:
- Always consider conversation history.
- If the user previously asked for events in a month/week, and is now updating or deleting an event, DO NOT narrow the date range too aggressively.
- For follow-up actions like "update" or "delete", preserve the original broader context to make sure the event is found.

PATTERNS:
- "today" → start: today 00:00:00, end: today 23:59:59
- "tomorrow" → start: tomorrow 00:00:00, end: tomorrow 23:59:59
- "this week" → start: Monday 00:00:00, end: Sunday 23:59:59
- "next week" → start: next Monday 00:00:00, end: next Sunday 23:59:59
- "this month" → start: 1st of month 00:00:00, end: last day 23:59:59
- If no date mentioned → default to TODAY.

SPECIAL RULES:
- When editing or deleting events, maintain the previous context (month/week) rather than switching to a single date.
- This avoids cases where an event isn't found due to an overly restrictive search.

OUTPUT:
- Return ISO format strings (YYYY-MM-DDTHH:MM:SS) without timezone info.
CURRENT TIME: {self._get_current_time()}
"""

    def _format_human_message(self, messages, user_query):
        return f"""CONVERSATION CONTEXT:
{self.formatter_without_tools(messages)}

USER REQUEST: "{user_query}"

Extract the most appropriate start and end dates for this request. 
If the user is referring to an event they already asked about, keep the same time range (e.g., month/week) to avoid missing it.
"""
