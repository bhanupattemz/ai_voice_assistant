from langchain_core.messages import SystemMessage, HumanMessage,AIMessage
from src.nodes.calendar.base_node import CalendarBaseNode
from src.config.settings import settings
from src.core.state import AssistantState
import datetime
from pydantic import BaseModel, Field


class DataOutput(BaseModel):
    can_make: bool = Field(
        description="Whether event can be deleted with provided information"
    )
    feedback: str = Field(
        description="Feedback message if event cannot be deleted or confirmation if it can"
    )
    event_id: str = Field(description="ID of the event to delete")


class DeleteCalendarNode(CalendarBaseNode):
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
           
            response = self.delete_reminder(
                res_data.event_id, 
            )
            return {"messages": [AIMessage(content=response)]}

        except ValueError as e:
            return {
                "messages": [
                    AIMessage(content=f"Error parsing date: {str(e)}. Please specify a valid date and time.")
                ]
            }
        except Exception as e:
            return {"messages": [AIMessage(content=f"Failed to Delete event: {str(e)}")]}

    def delete_reminder(self,event_id):
        service = self.get_calendar_service()
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return f"event deleted Success"
        except Exception as e:
            return f"Failed to delete error: {str(e)}"

    def get_system_message(self, state):
        calendar_events = state.get("calendar_events", [])
        calendar_details = ""
    
        if calendar_events:
            calendar_details = "\nAVAILABLE EVENTS TO DELETE:"
            for i, event in enumerate(calendar_events, 1):
                event_id = event.get("id", "No ID")
                summary = event.get("summary", "Untitled Event")
    
                start_info = event.get("start", {})
                start_datetime = start_info.get("dateTime", start_info.get("date", "No time"))
    
                end_info = event.get("end", {})
                end_datetime = end_info.get("dateTime", end_info.get("date", ""))
    
                calendar_details += f"\n{i}. ID: {event_id}"
                calendar_details += f"\n   Name: {summary}"
                calendar_details += f"\n   Start: {start_datetime}"
                if end_datetime:
                    calendar_details += f"\n   End: {end_datetime}"
                calendar_details += "\n"
        else:
            calendar_details = "\nNo events available to delete."
    
        return f"""You are an **event delete assistant** that extracts structured information from user requests to delete calendar events.
    
    ROLE:
    - Identify the correct event to delete.
    - Ensure user confirmation before deletion.
    - Output ONLY the fields defined in the schema (can_make, feedback, event_id).
    
    CURRENT TIME: {self._get_current_time()}
    
    {calendar_details}
    
    ### EXTRACTION RULES
    1) **can_make** = True **only if**:
       - You can unambiguously identify which event to delete (**event_id is known from the list above**), **and**
       - The user has **explicitly confirmed** deletion in the conversation.
         - Treat as confirmed if the latest user message includes both delete intent and an explicit confirmation (e.g., "yes, delete it", "confirm delete", "go ahead and delete").
         - Or if earlier the assistant asked to confirm and the user subsequently replied affirmatively (e.g., "yes", "confirm", "proceed", "delete it").
    2) **event_id**: REQUIRED when can_make=True. **Never invent IDs; use an ID from the list above only.**
    3) **feedback**: Always provide a concise, helpful message:
       - If can_make=True: confirm what will be deleted (event name/time if available).
       - If can_make=False: ask for missing info (which event?) or ask for explicit confirmation.
    
    ### INTENT & IDENTIFICATION
    - Delete intent keywords: **delete, remove, cancel, discard, clear, erase, drop, trash**.
    - Identify the event by matching user references (name, date/time, index like "the second event", or exact ID) against the list above.
    - If multiple events match or it’s ambiguous → set can_make=false and ask the user to specify the event (name/time/ID).
    - If there are **no events available**, set can_make=false with feedback indicating that there are no deletable events.
    
    ### CONFIRMATION POLICY (MANDATORY)
    - Even if the user says "delete <event>", you must request or detect explicit confirmation before proceeding.
    - If confirmation is **not** present in the conversation, set **can_make=false** and return feedback like:
      "I found '<EVENT_NAME>' scheduled <WHEN>. Do you want me to delete it? Reply 'yes' to confirm."
    - If the event appears to be part of a series (recurring), and scope is unclear:
      - set **can_make=false** and ask: "Delete just this occurrence or the entire series?"
    
    ### EXAMPLES
    - "delete project meeting" → If a single 'Project Meeting' exists, **ask to confirm**. When user confirms, can_make=true with that event_id.
    - "remove tomorrow's standup" → Identify the event by date; ask to confirm; on 'yes', can_make=true.
    - "yes, delete the 2nd event" (after listing) → map to the 2nd item’s ID; can_make=true.
    
    ### REQUIREMENTS SUMMARY
    - **event_id** is mandatory when can_make=True.
    - **Explicit confirmation** is mandatory; otherwise can_make=False with a confirmation prompt in feedback.
    - Do not modify any fields; your task is **delete-only**.
    """
    

    def _format_human_message(self, messages, user_query):
        return f"""CONVERSATION HISTORY:
    {self.formatter_without_tools(messages)}
    
    CURRENT REQUEST: "{user_query}"
    
    TASK: Identify which event the user wants to delete and verify that deletion is explicitly confirmed.
    
    ANALYSIS STEPS:
    1. Determine if the user expresses delete intent (delete/remove/cancel/discard/clear/erase/drop/trash).
    2. Identify the specific event:
       - Match by name, date/time, index (e.g., "the second one"), or exact ID from AVAILABLE EVENTS.
       - If ambiguous or multiple matches, prepare feedback asking the user to specify.
    3. Check for explicit confirmation:
       - Same-turn confirmation (e.g., "yes, delete it", "confirm delete").
       - Or prior assistant confirmation prompt followed by user's affirmative reply.
    4. If both event_id is known AND confirmation is explicit → can_make=true.
    5. Otherwise → can_make=false with helpful feedback:
       - If event unclear: ask which event (include likely matches).
       - If confirmation missing: ask for explicit confirmation to delete the identified event.
    
    OUTPUT: Provide only the fields required by the schema (can_make, feedback, event_id)."""
