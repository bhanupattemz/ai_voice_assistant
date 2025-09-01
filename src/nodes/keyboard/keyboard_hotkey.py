from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.nodes.keyboard.base_node import BaseNode
from src.core.state import AssistantState
from pydantic import BaseModel, Field
import pyautogui
import time
import logging

class DataOutput(BaseModel):
    not_related:bool=Field(description="set it true when user ask unrelated question else false")
    args: list[str] = Field(description="list of parameter to pass into press as keys")
    reasoning: str = Field(description="explanation of why these keys were chosen or reason for not_related is true", default="")


class KeyboardHotKeyNode(BaseNode):
    def __init__(self):
        super().__init__()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
    async def execute(self, state) -> AssistantState:
        """Node that processes keyboard input requests."""
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
            if not self._validate_keys(response.args):
                error_msg = f"Invalid keys detected: {response.args}. Only supported keys are allowed."
                logging.warning(error_msg)
                return {"messages": [AIMessage(content=error_msg)]}
            
            result = self.use_hotkey(response.args)
            response_content = f"Executed hotkey: {' + '.join(response.args)}"
            if response.reasoning:
                response_content += f"\nReasoning: {response.reasoning}"
                
            return {"messages": [AIMessage(content=response_content)]}
            
        except Exception as e:
            logging.error(f"Error in KeyboardFuncNode.execute: {str(e)}")
            return {"messages": [AIMessage(content=f"Error executing keyboard command: {str(e)}")]}
    
    def _validate_keys(self, keys: list[str]) -> bool:
        """Validate that all keys are in the allowed list."""
        if not keys or len(keys) < 2 or len(keys) > 3:
            return False
        
        normalized_keys = [key.lower() for key in keys]
        return all(key in self.ALL_KEYS for key in normalized_keys)
    
    def use_hotkey(self, keys: list[str]) -> str:
        """Press a hotkey combination with 2 or 3 keys."""
        try:
            if len(keys) not in (2, 3):
                raise ValueError("Hotkey function supports only 2 or 3 keys.")
            
            normalized_keys = [key.lower() for key in keys]
            
            logging.info(f"Pressing hotkey: {' + '.join(normalized_keys)}")
            pyautogui.hotkey(*normalized_keys)
            
            return f"Hotkey {' + '.join(normalized_keys)} pressed successfully"
            
        except Exception as e:
            error_msg = f"Failed to press hotkey {' + '.join(keys)}: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)

    def get_system_message(self) -> str:
        return f"""
    You are a keyboard shortcut assistant. Your job is to analyze user requests and determine the appropriate keyboard shortcuts to execute.
    
    Available keys: {', '.join(self.ALL_KEYS)}
    
    Guidelines:
    - Only return 2-3 keys maximum for hotkey combinations.
    - Common shortcuts: ctrl+c (copy), ctrl+v (paste), ctrl+z (undo), alt+tab (switch apps), etc.
    - Always use lowercase for all keys.
    - Provide reasoning for your choice.
    - If the request is unclear or unsafe, choose safe default keys like ['ctrl', 'shift'].
    - If the user asks a question unrelated to keyboard actions (e.g., "What time is it?"), set `not_related` to True and explain why; do not execute any keypresses.
    
    Examples:
    - "copy this" → ['ctrl', 'c']
    - "paste" → ['ctrl', 'v']
    - "undo" → ['ctrl', 'z']
    - "switch window" → ['alt', 'tab']
    - "refresh page" → ['ctrl', 'r']
    - "what is the current time?" → set `not_related` = True, give reasoning, exit keyboard mode
    """

    def _extract_latest_user_query(self, messages):
        """Extract the most recent user message."""
        from langchain_core.messages import HumanMessage

        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        """Format the human message for the LLM."""
        return f"""
Current user request: {user_query}

Recent conversation context:
{self.formatter_without_tools(messages)}

Please analyze the user's request and provide the appropriate keyboard shortcut.
"""