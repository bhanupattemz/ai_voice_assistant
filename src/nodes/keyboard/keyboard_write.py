from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.nodes.keyboard.base_node import BaseNode
from src.core.state import AssistantState
from pydantic import BaseModel, Field
import pyautogui
import time
import logging

class DataOutput(BaseModel):
    not_related: bool = Field(
        description="Set True if the user asks an unrelated question, else False"
    )
    text: str = Field(description="Text string to type")
    interval: float = Field(description="Interval between keystrokes in seconds", default=0.05)
    reasoning: str = Field(
        description="Explanation of why this text was chosen or why not_related is True",
        default=""
    )

class KeyboardWriteNode(BaseNode):
    def __init__(self):
        super().__init__()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    async def execute(self, state) -> AssistantState:
        try:
            system_msg = self.get_system_message()
            user_query = self._extract_latest_user_query(state["messages"])

            if not user_query:
                return {"messages": [AIMessage(content="No user query found to process.")]}

            human_msg = self._format_human_message(state["messages"], user_query)
            messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

            llm = self.llm_service.llm.with_structured_output(DataOutput)
            response = await llm.ainvoke(messages)

            if response.not_related:
                return {"messages": [AIMessage(content=response.reasoning)]}

            # Validate text before typing
            if not self._validate_text(response.text):
                error_msg = "Invalid text detected or text too long. Maximum 500 characters allowed."
                logging.warning(error_msg)
                return {"messages": [AIMessage(content=error_msg)]}

            # Execute typing
            result = self.write_text(response.text, response.interval)

            response_content = f"Typed text: '{response.text[:50]}{'...' if len(response.text) > 50 else ''}'"
            if response.reasoning:
                response_content += f"\nReasoning: {response.reasoning}"

            return {"messages": [AIMessage(content=response_content)]}

        except Exception as e:
            logging.error(f"Error in KeyboardWriteNode.execute: {str(e)}")
            return {"messages": [AIMessage(content=f"Error executing keyboard command: {str(e)}")]}

    def _validate_text(self, text: str) -> bool:
        return bool(text) and len(text) <= 500

    def write_text(self, text: str, interval: float = 0.05):
        pyautogui.write(text, interval=interval)
        time.sleep(0.5)
        return f"Typed text: '{text}' successfully"

    def get_system_message(self) -> str:
        return f"""
You are a text typing assistant. Your job is to analyze user requests and determine the appropriate text to type.

Guidelines:
- Extract the exact text the user wants to type
- Keep text under 500 characters for safety
- Use default interval of 0.05 seconds between keystrokes (adjust if user requests faster/slower)
- Provide reasoning for your choice
- If the user asks a question unrelated to typing, set `not_related` to True and provide reasoning

Examples:
- "type hello world" → 'hello world'
- "write my email address" → extract from context if available
- "type the date" → current date
- "enter my name" → extract from context if available
- "what time is it?" → set `not_related` = True, give reasoning, exit keyboard mode

Special considerations:
- For sensitive information, be cautious
- For long text, consider if it's appropriate
- Maintain user privacy and security
"""

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""
Current user request: {user_query}

Recent conversation context:
{self.formatter(messages)[-1000:] if hasattr(self, 'formatter') else 'No context available'}

Please analyze the user's request and provide the appropriate text to type, or set `not_related` if unrelated.
"""
