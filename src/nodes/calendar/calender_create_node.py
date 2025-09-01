from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.nodes.calendar.base_node import CalendarBaseNode
from src.config.settings import settings
from src.core.state import AssistantState
import datetime
from pydantic import BaseModel, Field


class DataOutput(BaseModel):
    can_make: bool = Field(
        description="Whether event can be created with provided information"
    )
    feedback: str = Field(
        description="Feedback message if event cannot be created or confirmation if it can"
    )
    name: str = Field(description="Name/title of the event", default="")
    start_date: str = Field(
        description="Event START date/time in ISO format (YYYY-MM-DDTHH:MM:SS)",
        default="",
    )
    end_date: str = Field(
        description="Event END date/time in ISO format (YYYY-MM-DDTHH:MM:SS)",
        default="",
    )
    description: str = Field(description="Description of the event", default="")


class CreateCalendarNode(CalendarBaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

        llm = self.llm_service.llm.with_structured_output(DataOutput)
        res_data = await llm.ainvoke(messages)

        if not res_data.can_make:
            return {"feedback": res_data.feedback}

        try:
            start_date = datetime.datetime.fromisoformat(
                res_data.start_date.replace("Z", "")
            )
            end_date = datetime.datetime.fromisoformat(
                res_data.end_date.replace("Z", "")
            )

            response = self.set_reminder(
                res_data.name, start_date, end_date, res_data.description
            )

            return {"messages": [AIMessage(content=response)]}

        except ValueError as e:
            return {
                "messages": [
                    AIMessage(content=f"Error parsing date: {str(e)}. Please specify a valid date and time.")
                ]
            }
        except Exception as e:
            return {"messages": [AIMessage(content=f"Failed to create event: {str(e)}")]}

    def set_reminder(self, name, start_dt, end_dt, description=None):
        try:
            service = self.get_calendar_service()
            event = {
                "summary": name,
                "description": description if description else "",
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": settings.timezone,
                },
                "end": {"dateTime": end_dt.isoformat(), "timeZone": settings.timezone},
                "reminders": {"useDefault": True},
            }
            created_event = (
                service.events().insert(calendarId="primary", body=event).execute()
            )

            start_formatted = start_dt.strftime("%B %d, %Y at %I:%M %p")
            end_formatted = end_dt.strftime("%I:%M %p")
            return f"Event '{name}' created successfully for {start_formatted} to {end_formatted}"

        except Exception as e:
            return f"Failed to create calendar event: {str(e)}"

    def get_system_message(self):
        return f"""You are an event creation assistant that extracts information from user requests.

ROLE: Parse user requests to create calendar events
CURRENT TIME: {self._get_current_time()}

EXTRACTION RULES:
1. **can_make**: Set to true only if you can extract NAME, START_DATE and END_DATE
2. **name**: Event title (required) - if not specified, create based on context
3. **start_date**: Event start time in ISO format YYYY-MM-DDTHH:MM:SS (required)
4. **end_date**: Event end time in ISO format YYYY-MM-DDTHH:MM:SS (required)
5. **description**: Optional details about the event
6. **feedback**: Always provide a message

DATE/TIME PARSING - BE VERY CAREFUL:
- "5PM to 6PM" → if no date specified, ask user to clarify which day
- "tomorrow 5PM to 6PM" → tomorrow's date at 17:00:00 to 18:00:00
- "project at 5PM to 6PM" → MUST specify which day, cannot assume
- "today 3:30pm" → today at 15:30:00
- "next Monday 10am to 11am" → next Monday 10:00:00 to 11:00:00

TIME CONVERSION (24-hour format):
- 1PM = 13:00:00, 2PM = 14:00:00, 3PM = 15:00:00
- 4PM = 16:00:00, 5PM = 17:00:00, 6PM = 18:00:00
- 7PM = 19:00:00, 8PM = 20:00:00, 9PM = 21:00:00

DATE ASSUMPTIONS:
- If ONLY time is given (no date), set can_make=false and ask for date
- If user says "tomorrow", "today", "next Monday" - use those specific dates
- Never assume a date if not specified

FEEDBACK EXAMPLES:
- can_make=true: "Creating event '[EVENT_NAME]' for [START] to [END]"
- can_make=false: "I need to know which day you want to schedule this event. Please specify the date."
- can_make=false: "I need both start and end times to create the event."

REQUIRED INFORMATION:
- Name is MANDATORY (generate if needed)
- Start date/time is MANDATORY
- End date/time is MANDATORY(add one hr to starting data if not mentioned)  
- If any missing, set can_make=false
"""

    def _format_human_message(self, messages, user_query):
        return f"""CONVERSATION HISTORY:
{self.formatter_without_tools(messages)}

CURRENT REQUEST: "{user_query}"

CRITICAL: Extract event information carefully:
1. Event name (generate if not provided)
2. START date and time - convert to ISO format with correct time
3. END date and time - convert to ISO format with correct time
4. If date is not specified, set can_make=false

EXAMPLES:
- "meeting tomorrow 5PM to 6PM" → start_date: "2025-09-02T17:00:00", end_date: "2025-09-02T18:00:00"
- "call at 3PM" (no date) → can_make: false, feedback: "Which day do you want to schedule this?"

Parse the request and ensure times are correctly converted to 24-hour format in ISO string.
"""
