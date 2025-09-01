from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.nodes.calendar.base_node import CalendarBaseNode
from src.config.settings import settings
from src.core.state import AssistantState
import datetime
from pydantic import BaseModel, Field


class DataOutput(BaseModel):
    can_make: bool = Field(
        description="Whether event can be updated with provided information"
    )
    feedback: str = Field(
        description="Feedback message if event cannot be updated or confirmation if it can"
    )
    event_id: str = Field(description="ID of the event to update")
    name: str = Field(description="Updated name/title of the event", default="")
    start_date: str = Field(
        description="Updated event START date/time in ISO format (YYYY-MM-DDTHH:MM:SS)",
        default="",
    )
    end_date: str = Field(
        description="Updated event END date/time in ISO format (YYYY-MM-DDTHH:MM:SS)",
        default="",
    )
    description: str = Field(description="Updated description of the event", default="")


class UpdateCalendarNode(CalendarBaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message(state)
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

        llm = self.llm_service.llm.with_structured_output(DataOutput)
        res_data = await llm.ainvoke(messages)

        if not res_data.can_make:
            return {"feedback": res_data.feedback}

        try:
            # Parse dates only if provided
            start_date = None
            end_date = None

            if res_data.start_date:
                start_date = datetime.datetime.fromisoformat(
                    res_data.start_date.replace("Z", "")
                )

            if res_data.end_date:
                end_date = datetime.datetime.fromisoformat(
                    res_data.end_date.replace("Z", "")
                )

            response = self.update_reminder(
                res_data.event_id,
                start_date,
                end_date,
                res_data.name,
                res_data.description,
            )

            return {"messages": [AIMessage(content=response)]}

        except ValueError as e:
            return {
                "messages": [
                    f"Error parsing date: {str(e)}. Please specify a valid date and time."
                ]
            }
        except Exception as e:
            return {"messages": [f"Failed to update event: {str(e)}"]}

    def update_reminder(
        self, event_id, start_dt=None, end_dt=None, new_name=None, new_description=None
    ):
        try:
            service = self.get_calendar_service()

            event = (
                service.events().get(calendarId="primary", eventId=event_id).execute()
            )
            if start_dt and end_dt:
                event["start"]["dateTime"] = start_dt.isoformat()
                event["start"]["timeZone"] = "Asia/Kolkata"
                event["end"]["dateTime"] = end_dt.isoformat()
                event["end"]["timeZone"] = "Asia/Kolkata"

            if new_name:
                event["summary"] = new_name

            if new_description is not None:  
                event["description"] = new_description

            updated_event = (
                service.events()
                .update(calendarId="primary", eventId=event_id, body=event)
                .execute()
            )

            event_name = updated_event.get("summary", "Event")
            start_time = updated_event.get("start", {}).get("dateTime", "")

            if start_time:
                formatted_time = datetime.datetime.fromisoformat(
                    start_time.replace("Z", "")
                ).strftime("%B %d, %Y at %I:%M %p")
                return f"Updated '{event_name}' successfully for {formatted_time}"
            else:
                return f"Updated '{event_name}' successfully"

        except Exception as e:
            return f"Failed to update calendar event: {str(e)}"

    def get_system_message(self, state):
        calendar_events = state.get("calendar_events", [])
        calendar_details = ""

        if calendar_events:
            calendar_details = "\nAVAILABLE EVENTS TO UPDATE:"
            for i, event in enumerate(calendar_events, 1):
                event_id = event.get("id", "No ID")
                summary = event.get("summary", "Untitled Event")

                start_info = event.get("start", {})
                start_datetime = start_info.get(
                    "dateTime", start_info.get("date", "No time")
                )

                end_info = event.get("end", {})
                end_datetime = end_info.get("dateTime", end_info.get("date", ""))

                calendar_details += f"\n{i}. ID: {event_id}"
                calendar_details += f"\n   Name: {summary}"
                calendar_details += f"\n   Start: {start_datetime}"
                if end_datetime:
                    calendar_details += f"\n   End: {end_datetime}"
                calendar_details += "\n"
        else:
            calendar_details = "\nNo events available to update."

        return f"""You are an **event update assistant** that extracts structured information from user requests to update calendar events.
    
    ROLE:
    - Identify the correct event to update.
    - Extract only the fields the user wants to change.
    - Provide structured data for downstream systems.
    
    CURRENT TIME: {self._get_current_time()}
    
    {calendar_details}
    
    ### EXTRACTION RULES:
    1. **can_make**: True ONLY if you can identify which event to update AND at least one field to change.  
    2. **event_id**: REQUIRED. Must match one of the available event IDs above.  
    3. **name**: Only set if the user explicitly wants to rename the event.  
    4. **start_date**: Set only if the start time/date is being changed.  
    5. **end_date**:  
       - If explicitly given, set it.  
       - If missing but start_date is provided, set end_date = start_date + 1 hour.  
    6. **description**: Only set if explicitly mentioned.  
    7. **feedback**: Always provide a helpful confirmation or error message.  
    
    ---
    
    ### EVENT IDENTIFICATION:
    - Match events by **name, time, or position**.  
    - If multiple events match, request clarification.  
    - If no match, set `can_make=false`.  
    
    ---
    
    ### UPDATE BEHAVIOR:
    - Update ONLY fields the user mentions.  
    - Leave unspecified fields unchanged.  
    - Examples:  
      - "Change meeting to 3PM" → Update start_date (and end_date = start + 1 hour).  
      - "Rename team sync to standup" → Update name only.  
      - "Reschedule to Friday at 2PM" → Update both date and time.  
    
    ---
    
    ### DATE/TIME PARSING:
    - Natural phrases like "tomorrow" → Adjust date, keep time.  
    - "Move to next Monday at 5PM" → Update both date and time.  
    - If only time is given, use original date.  
    
    ---
    
    ### FEEDBACK EXAMPLES:
    - can_make=true: "Updating 'Project Meeting' with new time"  
    - can_make=false: "I couldn't find that event. Please specify which event to update."  
    - can_make=false: "I need to know which event to update and what changes to make."  
    
    ---
    
    ### REQUIREMENTS:
    - `event_id` and at least one changed field are mandatory.  
    - If missing, set `can_make=false`.  
    - Always infer `end_date` as start_date + 1 hour if missing.  
    """

    def _format_human_message(self, messages, user_query):
        return f"""CONVERSATION HISTORY:
{self.formatter_without_tools(messages)}

CURRENT REQUEST: "{user_query}"

TASK: Identify which event to update and what changes to make.

ANALYSIS STEPS:
1. Which event is the user referring to? (match by name, time, or description)
2. What specific changes do they want to make?
3. Extract the event ID from the available events
4. Parse any new dates/times relative to current time
5. Only include fields that the user wants to change

EXAMPLES:
- "change project meeting to 3PM" → find "project" event, update start_date to 15:00:00
- "move tomorrow's meeting to Friday" → find tomorrow's event, change date to Friday
- "rename team sync to standup" → find "team sync" event, update name to "standup"

Extract the update information carefully, ensuring you identify the correct event and changes.
"""
