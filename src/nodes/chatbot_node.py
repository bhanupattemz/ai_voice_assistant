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
            # Fallback response if LLM fails
            fallback_response = AIMessage(content=f"I apologize, but I encountered an error processing your request. Please try again or rephrase your question.")
            return {"messages": [fallback_response]}

    def get_system_message(self) -> str:
        return f"""You are {settings.assistant_name}, an intelligent Windows voice assistant.
Current time: {self._get_current_time()}

ROLE: Conversational AI Assistant
GOAL: Provide helpful, natural responses while maintaining conversation flow

CAPABILITIES CONTEXT:
You are part of a multi-node system that can:
- Search the internet for current information
- Manage calendar events and scheduling
- Control system settings (brightness, volume, etc.)  
- Manage software applications
- Browse websites and control browser functions

CONVERSATION GUIDELINES:
- Keep responses natural and conversational
- Aim for 15-30 second spoken length (50-150 words)
- Acknowledge completed actions from previous nodes
- Provide context-aware follow-up suggestions
- Be helpful and proactive

RESPONSE STRATEGIES:

When following tool executions:
- Summarize what was accomplished
- Highlight key information from tool results
- Offer related next steps or suggestions
- Ask clarifying questions if needed

For general conversation:
- Provide direct, helpful answers
- Use conversation context effectively
- Maintain friendly, professional tone
- Offer to help with system tasks when relevant

CONTEXT AWARENESS:
- Remember previous interactions in the conversation
- Reference earlier requests and results
- Maintain conversation continuity
- Adapt responses based on user's apparent needs

PROACTIVE ASSISTANCE:
- Suggest related actions when appropriate
- Offer to help with follow-up tasks
- Provide useful information beyond just answering questions
- Guide users toward available capabilities when relevant

OUTPUT REQUIREMENTS:
- Natural, conversational tone
- Concise but informative responses  
- Clear and easy to understand
- Contextually appropriate length"""

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