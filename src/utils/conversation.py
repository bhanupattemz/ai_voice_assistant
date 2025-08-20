from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

class ConversationFormatter:
    @staticmethod
    def format_conversation(messages) -> str:
        """Format conversation history for context."""
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                if message.content:
                    conversation += f"Assistant: {message.content}\n"
                else:
                    tool_calls = getattr(message, "tool_calls", [])
                    if tool_calls:
                        tools_used = ', '.join([call['name'] for call in tool_calls])
                        conversation += f"Assistant: \n"
            elif isinstance(message, ToolMessage):
                tool_name = getattr(message, "name", "Unknown Tool")
                content = message.content[:200] + "..." if len(message.content) > 200 else message.content
                conversation += f"Tool ({tool_name}): {content}\n"
        
        return conversation
