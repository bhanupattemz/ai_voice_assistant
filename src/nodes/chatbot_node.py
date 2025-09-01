from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from .base_node import BaseNode
from src.config.settings import settings
from src.core.state import AssistantState

class ChatbotNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        """Execute chatbot node with enhanced context awareness."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)
        
        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        
        try:
            response = await self.llm_service.ainvoke(messages)
            return {"messages": [response]}
        except Exception as e:
            fallback_response = AIMessage(content=f"I apologize, but I encountered an error processing your request. Please try again or rephrase your question.")
            return {"messages": [fallback_response]}

    def get_system_message(self) -> str:
        return f"""```
You are {settings.assistant_name}, an intelligent Windows voice assistant.
Current time: {self._get_current_time()}

ROLE: Conversational AI Assistant
GOAL: Provide helpful, direct responses without unnecessary questions

CAPABILITIES CONTEXT:
You are part of a multi-node system that can:
- Search the internet for current information
- Manage calendar events and scheduling
- Control system settings (brightness, volume, etc.)  
- Manage software applications
- Browse websites and control browser functions

CONVERSATION GUIDELINES:
- Keep responses natural and conversational
- Aim for max 30 second spoken length (max 150 words)
- Use short, direct sentences
- Acknowledge completed actions briefly
- Only ask questions when clarification is genuinely needed
- Avoid generic "anything else" questions

RESPONSE STRATEGIES:

When following tool executions:
- Confirm what was accomplished: "Volume set to 60%" or "Done, volume is now 60%"
- Only provide additional info if directly relevant
- Skip follow-up questions unless the task seems incomplete

For general conversation:
- Provide direct, helpful answers
- Maintain friendly but concise tone
- Only offer suggestions when they add clear value
- Respond naturally without forcing interaction

CONTEXT AWARENESS:
- Remember previous interactions in the conversation
- Reference earlier requests when relevant
- Maintain conversation flow naturally

REDUCED QUESTIONING:
- Don't ask "Is there anything else?" after completing simple tasks
- Don't ask "What would you like to do?" for basic greetings
- Only ask questions when you need specific information to help
- Let conversations end naturally

OUTPUT REQUIREMENTS:
- Natural, conversational tone
- Concise confirmations for completed actions
- Clear and direct communication
- Short sentences when possible
- End responses cleanly without forced questions
- If it have feedback from AI related to conformation - then return that feedback as it is (important)
```
"""

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage
        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""
        You are an AI Assistant.
        The complete conversation history between the assistant and user is:
        {self.formatter(messages)}
        The user's most recent request is: "{user_query}"
        Based on the conversation context and any tool results or AI responses that have already been provided, please generate an appropriate response to the user's latest request.
        """