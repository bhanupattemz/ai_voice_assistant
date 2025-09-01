from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.nodes.calendar.base_node import CalendarBaseNode
from src.config.settings import settings
from src.core.state import AssistantState


class FinalCalendarNode(CalendarBaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        system_msg = self.get_system_message(state)
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query, state)
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        
        response = await self.llm_service.ainvoke(messages)
        
        return {"messages": [AIMessage(content=response.content)],"feedback":None}
    
    def get_system_message(self,state):
        return f"""You are a calendar data summarizer that prepares comprehensive information for the chatbot.

ROLE: Calendar operation data compiler
CURRENT TIME: {self._get_current_time()}

TASK: Provide complete, detailed information about calendar operations for the chatbot to respond to the user.
Feedback:
{state.get("feedback","")}
GUIDELINES:
- Include ALL relevant details from calendar operations
- List EVERY event with complete information (name, date, time)
- Provide specific data, not summaries like "3 events" or "several meetings"
- Include creation confirmations with full event details
- Mention any errors or missing information explicitly
- Be comprehensive and factual - the chatbot will make this conversational
- If feedback related to conformation - then return that feedback as it is (important)

DATA TO INCLUDE:
For event viewing:
- Complete list of all events found
- Event names, dates, times, descriptions
- If no events found, state that explicitly

For event creation:
- Confirmation of what was created
- Complete event details (name, start time, end time, date)
- Any errors or issues that occurred

For errors:
- Specific reason for failure
- What information was missing
- What the user needs to provide

OUTPUT FORMAT:
Provide structured, complete information that gives the chatbot everything needed to respond naturally to the user.
"""

    def _format_human_message(self, messages, user_query, state):
        calendar_events = state.get("calendar_events", [])
        calendar_details = ""
        if "calendar_events" in state:
            if len(calendar_events) == 0:
                calendar_details = "\nCalendar Query Results: No events found for the requested time period."
            else:
                calendar_details = "\nCalendar Query Results:"
                for i, event in enumerate(calendar_events, 1):
                    summary = event.get('summary', 'Untitled Event')
                    
                    start_info = event.get('start', {})
                    start_datetime = start_info.get('dateTime', start_info.get('date', 'No time specified'))
                    
                    end_info = event.get('end', {})
                    end_datetime = end_info.get('dateTime', end_info.get('date', ''))
                    
                    description = event.get('description', '')
                    
                    location = event.get('location', '')
                    
                    event_details = f"\n{i}. Event: {summary}"
                    event_details += f"\n   Start: {start_datetime}"
                    if end_datetime and end_datetime != start_datetime:
                        event_details += f"\n   End: {end_datetime}"
                    if description:
                        event_details += f"\n   Description: {description}"
                    if location:
                        event_details += f"\n   Location: {location}"
                    
                    calendar_details += event_details
        
        operation_results = ""
        recent_messages = messages[-3:] if len(messages) > 3 else messages
        for msg in recent_messages:
            content = str(msg.content) if hasattr(msg, 'content') else str(msg)
            if any(keyword in content.lower() for keyword in ['created successfully', 'failed to create', 'error', 'couldn\'t create']):
                operation_results += f"\nOperation Result: {content}"

        return f"""CONVERSATION HISTORY:
{self.formatter_without_tools(messages)}

USER'S REQUEST: "{user_query}"

CALENDAR DATA RETRIEVED:{calendar_details}

OPERATION RESULTS:{operation_results}

TASK: Compile all calendar information for the chatbot response.
Include every event with complete details, all operation results, and any relevant information.
The chatbot will use this to provide a natural, conversational response to the user.
Be comprehensive - don't summarize or count events, list them all with full details.
"""