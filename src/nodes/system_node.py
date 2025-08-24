import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_node import BaseNode
from src.config.settings import settings
from src.core.state import AssistantState
from src.tools.system_tools import system_tools

class SystemNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        """Node that decides whether to use a System tool (sync version)."""
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])

        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        
        try:
            llm = await self.llm_service.abind_tools(system_tools)
            response = await llm.ainvoke(messages, tool_choice="auto")
        except:
            try:
                llm = await self.llm_service.abind_tools(system_tools)
                response = await llm.ainvoke(messages)
            except:
                llm = self.llm_service.bind_tools(system_tools)
                response = await llm.ainvoke(messages)
            
        return {"messages": [response]}

    def get_system_message(self) -> str:
        return f"""
        You are {settings.assistant_name}, an AI voice assistant for Windows.
        Current time: {self._get_current_time()}
    
        === SYSTEM CONTROL NODE ===
        You MUST use the appropriate tool function calls to control the system. 
        DO NOT respond with text explanations.
    
        AVAILABLE TOOLS (MUST USE FUNCTION CALLS):
    
        1. **brightness_control(integer)**  
           - Controls display screen brightness (0-100)
           - USE FOR: brightness, bright, dim, screen light, display brightness, illumination
           - EXAMPLES: "increase brightness", "dim screen", "set brightness to 75%"
           - CALL: brightness_control(value) where value is 0-100
    
        2. **volume_control(integer)**
           - Controls system audio volume (0-100)  
           - USE FOR: volume, sound, audio, mute, louder, quieter, speaker volume
           - EXAMPLES: "turn up volume", "mute audio", "set volume to 50%"
           - CALL: volume_control(value) where value is 0-100
    
        3. **system_performance_monitor()**
           - Retrieves comprehensive system metrics and hardware status
           - USE FOR: CPU usage, RAM usage, GPU performance, disk usage, network speed, temperatures, system diagnostics
           - EXAMPLES:
               - "Check CPU" → system_performance_monitor()
               - "How much RAM is being used?" → system_performance_monitor()
               - "GPU performance" → system_performance_monitor()
               - "System status" → system_performance_monitor()
           - NOTE: Always call system_performance_monitor() for any hardware/system info requests.
                   If the query mentions a specific component (e.g., GPU), highlight that component’s metrics 
                   in your response while including full system information.
    
        4. **quick_settings(string)**
           - Toggles Windows Quick Settings (Wi-Fi, Bluetooth, Airplane Mode, Mobile Hotspot, Energy Saver, Night Light)
           - USE FOR: enabling/disabling connectivity or quick settings features
           - Accepted values:
               * By name → ["wifi", "bluetooth", "airplane", "hotspot", "saver", "night"]
               * By position → "qsN" where N = button number (qs1–qs9)
           - EXAMPLES:
               - "turn on Wi-Fi" → quick_settings("wifi")
               - "disable Bluetooth" → quick_settings("bluetooth")
               - "toggle airplane mode" → quick_settings("airplane")
               - "qs3" → quick_settings("qs3")
    
        CRITICAL EXECUTION RULES:
        - You MUST use actual function calls, NOT text responses
        - When user requests any system action, immediately call the appropriate function
        - DO NOT explain what you're going to do - just execute the function call
        - DO NOT simulate or describe the function call in text
        - The function will return the actual result - don't predict or simulate results
        - If unsure about exact values, use reasonable defaults based on context
    
        FUNCTION CALL EXAMPLES:
        WRONG: "I'll call brightness_control(80)" 
        CORRECT: Actually call brightness_control(80)
    
        WRONG: "Let me check your system performance..."
        CORRECT: Actually call system_performance_monitor()
    
        VALUE INTERPRETATION GUIDELINES:
        - "increase/raise/up" = add 20-30 to current assumption (default to 70-80)
        - "decrease/lower/down" = subtract 20-30 from current assumption (default to 30-40) 
        - "medium/normal" = use 50
        - "high/max/full" = use 80-100
        - "low/min" = use 10-30
        - "mute/silent" = use 0
        - "on/off" = use quick_settings("...") for relevant settings
        - For specific hardware requests (CPU, GPU, RAM, Disk, Network), call system_performance_monitor()
          and highlight the relevant component metrics in the returned output.
        
        EXECUTE FUNCTION CALLS IMMEDIATELY UPON REQUEST.
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
        USER REQUEST: "{user_query}"
    
        TASK: Analyze the user request and call the appropriate system function immediately.
    
        DECISION MATRIX:
        - Wireless/Connectivity: airplanemode_control(), bluetooth_control(), wifi_control(), hotspot_control()
        - Display: brightness_control(0-100)
        - Audio: volume_control(0-100) 
        - System Info: system_performance_monitor()
    
        EXECUTION INSTRUCTION:
        Make the function call now. Do not explain, describe, or simulate - actually execute the function.
    
        Remember: 
        - For percentage requests: extract the number (e.g., "50%" → 50)
        - For relative requests: use reasonable defaults (bright=80, dim=30, loud=80, quiet=20)
        - For on/off requests: use true/false appropriately
        - For status/info requests: call system_performance_monitor()
    
        EXECUTE THE FUNCTION CALL IMMEDIATELY.
        """

   
   