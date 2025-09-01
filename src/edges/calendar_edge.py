import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_edge import BaseEdge


class CalendarRedirectorEdge(BaseEdge):
    def __init__(self):
        super().__init__()

    async def execute(self, state):
        """Edge that decides the next node with improved routing logic."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query, state)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        
        try:
            response = await self.llm_service.ainvoke(messages, use_pro=True)
            result = response.content.strip().lower()
            
            valid_nodes = {
                "calendar_create",
                "calendar_update",
                "calendar_delete",
                "calendar_final"
            }
            
            print(f"Calendar Router decision: {result}")
            
            if result in valid_nodes:
                return result
            else:
                print(f"Invalid router result '{result}', defaulting to calendar_final")
                return "calendar_final"
                
        except Exception as e:
            print(f"Router error: {e}, defaulting to calendar_final")
            return "calendar_final"

    def get_system_message(self) -> str:
        return """You are a calendar request router that determines which calendar operation to perform.
    
    ROLE: Calendar Request Classifier
    GOAL: Route requests to the appropriate calendar processing node
    
    AVAILABLE ROUTES:
    1. **calendar_create** - For creating new events, meetings, appointments, reminders
       - Keywords: create, schedule, add, book, set reminder, make appointment, plan
       - Examples: "schedule meeting tomorrow", "create event for Friday", "remind me to call"
    
    2. **calendar_update** - For modifying or rescheduling existing events
       - Keywords: change, reschedule, move, update, edit, rename, postpone, delay, shift
       - Examples: "reschedule team sync to Friday", "change project meeting to 3PM", "rename daily standup"
    
    3. **calendar_delete** - For removing or cancelling events
       - Keywords: delete, remove, cancel, clear, discard, drop, erase
       - Examples: "delete my 5 PM meeting", "cancel dinner on Friday", "remove all reminders"
    
    4. **calendar_final** - For all other operations including viewing events, checking calendar, or confirming actions
       - Keywords: show, check, view, what's on, list, find events, completed operations
       - Examples: "what's on my calendar today", "show tomorrow's events", "list all meetings"
    
    ROUTING RULES:
    - **calendar_create** → ONLY when user clearly wants to create or add a new calendar entry
    - **calendar_update** → ONLY when user clearly wants to modify an existing entry
    - **calendar_delete** → ONLY when user explicitly wants to cancel, delete, or remove an event
    - **calendar_final** → For everything else (viewing, confirming, non-actionable requests)
    - Prioritize update or delete intent over create or final when explicit
    
    OUTPUT FORMAT:
    Return only ONE of: calendar_create, calendar_update, calendar_delete, calendar_final
    """



    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query, state):
       
        has_calendar_data = "calendar_events" in state or "calender_events" in state
        
        conversation_context = self.formatter(messages)
        
        context_hints = ""
        if has_calendar_data:
            context_hints += "\n- Previous operation retrieved calendar data"
        
        if "created successfully" in conversation_context.lower() or "event created" in conversation_context.lower():
            context_hints += "\n- Previous operation completed event creation"
            
        return f"""CALENDAR REQUEST ANALYSIS

USER REQUEST: "{user_query}"

CONVERSATION CONTEXT:
{conversation_context}

STATE CONTEXT:{context_hints}

CLASSIFICATION TASK:
Determine the primary calendar operation needed:

1. Does user want to CREATE something new?
   - Look for: schedule, create, add, book, set reminder, make appointment, plan
   - Route to: calendar_create

2. Everything else (viewing, checking, completed operations, unclear intent):
   - Look for: show, check, what's on, view, list, see my calendar
   - Previous operations that are complete
   - Any non-creation request
   - Route to: calendar_final

ROUTING DECISION:
Based on the user's request and context, what calendar operation is needed?"""