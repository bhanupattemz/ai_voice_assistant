import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from .base_edge import BaseEdge


class RedirectorEdge(BaseEdge):
    def __init__(self):
        super().__init__()

    async def execute(self, state):
        """Edge that decides the next node with improved routing logic."""
        if state.get("mode","normal")=="keyboard":
            print("selected: keyboard_node")
            return "keyboard_node"
        
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        
        try:
            response = await self.llm_service.ainvoke(messages, use_pro=True)
            result = response.content.strip().lower()
            
            valid_nodes = {
                "chatbot",
                "network_search", 
                "calendar_node",
                "browser_node",
                "system_node", 
                "software_node",
                "keyboard_node"
            }
            
            print(f"Router decision: {result}")
            
            if result in valid_nodes:
                return result
            else:
                print(f"Invalid router result '{result}', defaulting to chatbot")
                return "chatbot"
                
        except Exception as e:
            print(f"Router error: {e}, defaulting to chatbot")
            return "chatbot"

    def get_system_message(self) -> str:
        return """You are an intelligent request router that analyzes user messages and determines the appropriate system component to handle them.

ROLE: Request Classification Specialist
GOAL: Route requests to the most appropriate processing node

AVAILABLE ROUTES:
1. network_search - Internet searches, current information, news, weather, Wikipedia
2. calendar_node - Calendar operations, events, meetings, scheduling
3. browser_node - Web browser control and navigation
4. system_node - System controls (brightness, volume, performance monitoring)
5. software_node - Application management (launch, check, security scans)
6. keyboard_node - when user want to turn on keyboard mode
7. chatbot - General conversation, questions answerable without tools



ROUTING DECISION MATRIX:

→ network_search
TRIGGERS: search, google, find information, news, weather, wikipedia, current events, recent updates
EXAMPLES: "search for AI news", "what's the weather", "find recent studies"

→ calendar_node  
TRIGGERS: calendar, schedule, meeting, event, appointment, book, plan, remind
EXAMPLES: "check my calendar", "schedule meeting", "what events tomorrow"

→ browser_node
TRIGGERS: browser, website, navigate, open site, web page, url, bookmark
EXAMPLES: "open google.com", "navigate to website", "close browser"

→ system_node
TRIGGERS: brightness, volume, sound, airplane mode, wifi, bluetooth, CPU, RAM, GPU, performance, system info
EXAMPLES: "increase brightness", "check CPU usage", "mute volume"

→ software_node
TRIGGERS: open app, launch, start program, run software, install, virus scan, malware check
EXAMPLES: "open chrome", "launch calculator", "scan for viruses"

→ keyboard_node
TRIGGERS: when user want to set keyboard mode
EXAMPLES: "set keyboard mode", "keyboard", "keyboard mode"

→ chatbot
TRIGGERS: general questions, explanations, help, advice, casual conversation
EXAMPLES: "how does photosynthesis work", "tell me a joke", "explain quantum physics"

OUTPUT REQUIREMENT:
Return EXACTLY ONE word from: network_search, calendar_node, browser_node, system_node, software_node, keyboard_node, chatbot

CRITICAL RULES:
- Analyze the PRIMARY intent of the user's request
- Choose the most specific applicable route
- When in doubt between routes, prefer the more specific tool-based option
- Only use "chatbot" for general knowledge questions that don't require system interaction

Return only the single routing word, nothing else."""

    def _extract_latest_user_query(self, messages):
        from langchain_core.messages import HumanMessage

        for i in range(len(messages) - 1, -1, -1):
            latest_message = messages[i]
            if isinstance(latest_message, HumanMessage):
                return latest_message.content
        return ""

    def _format_human_message(self, messages, user_query):
        return f"""ROUTING ANALYSIS REQUIRED

CURRENT USER REQUEST: "{user_query}"

CONVERSATION CONTEXT:
{self.formatter(messages)}

ROUTING INSTRUCTIONS:
1. Identify the PRIMARY action the user wants to perform
2. Match request to the most appropriate system component
3. Consider conversation context for continuation patterns
4. Check if this is a follow-up to a previous action

CONTEXT ANALYSIS:
- Is this a new request or follow-up to previous interaction?
- Does the user need external information or system control?
- Is this a general conversation or specific task?
- Has the current task been completed?

REQUEST CLASSIFICATION:
Analyze user intent and classify into ONE category:
- Information seeking → network_search
- Calendar operations → calendar_node  
- Browser control → browser_node
- System control → system_node
- Software management → software_node
- General conversation → chatbot

DECISION FACTORS:
- Keywords and action verbs in the request
- Type of information or action needed
- Context from previous interactions
- Specificity of the request

Output the single most appropriate routing decision."""