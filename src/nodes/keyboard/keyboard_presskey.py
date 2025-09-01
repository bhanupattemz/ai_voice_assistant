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
    key: str = Field(description="Single key to press")
    reasoning: str = Field(
        description="Explanation of why this key was chosen or why not_related is True",
        default=""
    )

class KeyboardPressNode(BaseNode):
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

            if not self._validate_key(response.key):
                error_msg = f"Invalid key detected: {response.key}. Only supported keys are allowed."
                logging.warning(error_msg)
                return {"messages": [AIMessage(content=error_msg)]}

            result = self.press_key(response.key)

            response_content = f"Pressed key: {response.key}"
            if response.reasoning:
                response_content += f"\nReasoning: {response.reasoning}"

            return {"messages": [AIMessage(content=response_content)]}

        except Exception as e:
            logging.error(f"Error in KeyboardPressNode.execute: {str(e)}")
            return {"messages": [AIMessage(content=f"Error executing keyboard command: {str(e)}")]}

    def _validate_key(self, key: str) -> bool:
        if not key:
            return False
        return key.lower() in [k.lower() for k in self.ALL_KEYS]

    def press_key(self, key: str):
        if key not in self.ALL_KEYS:
            raise ValueError(f"Invalid key: {key}")
        pyautogui.press(key)
        time.sleep(0.5)
        return f"Key '{key}' pressed successfully"

    def get_system_message(self) -> str:
        return f"""
You are a single key press assistant. Your job is to analyze user requests and determine the appropriate single key to press.

Available keys: {', '.join(self.ALL_KEYS)}

Guidelines:
- Only return ONE key to press
- Use lowercase for all keys
- Provide reasoning for your choice
- If the user asks a question unrelated to keyboard actions, set `not_related` to True and provide reasoning
- Common single keys: enter, space, tab, esc, backspace, delete, etc.
- For navigation: up, down, left, right, home, end
- For function keys: f1, f2, f3, etc.

Examples:
- "press enter" → 'enter'
- "go to next line" → 'enter'
- "delete character" → 'backspace'
- "move cursor up" → 'up'
- "press space" → 'space'
- "escape" → 'esc'
- "what is the time?" → set `not_related` = True, give reasoning, exit keyboard mode
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
{self.formatter(messages)}

Please analyze the user's request and provide the appropriate single key to press or set `not_related` if unrelated.
"""
