from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.nodes.base_node import BaseNode
from src.config.settings import settings
from src.core.state import AssistantState
from src.tools.browser_tools import browser_tools
from langchain_community.tools import YouTubeSearchTool
from pydantic import BaseModel, Field
import webbrowser


class DataOutput(BaseModel):
    not_related: bool = Field(
        description="set it true when user ask unrelated question else false"
    )
    search_text: str = Field(description="The Text that need to search in youtube")
    reasoning: str = Field(
        description="reason for not_related is true or final respounse text if search",
        default="",
    )
    play_directly: bool = Field(
        description="True does user want to play directly the reasech result else false "
    )


class YoutubeNode(BaseNode):
    def __init__(self):
        super().__init__()

    async def execute(self, state) -> AssistantState:
        search_tool = YouTubeSearchTool()
        system_msg = self.get_system_message()
        user_query = self._extract_latest_user_query(state["messages"])
        human_msg = self._format_human_message(state["messages"], user_query)

        messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
        llm = self.llm_service.llm.with_structured_output(DataOutput)
        response = await llm.ainvoke(messages)
        if response.not_related:
            return {"messages": [AIMessage(content=response.reasoning)]}
        if not response.play_directly:
             webbrowser.open(
                    f"https://www.youtube.com/results?search_query={response.search_text.replace(" ","+")}"
                )
               
        else:
            search_links = search_tool.run(response.search_text)
            search_links=search_links.replace("'","")
            search_links= search_links[1:-1].split(",")
            webbrowser.open(search_links[0])
        return {"messages": [AIMessage(content=response.reasoning)]}

    def get_system_message(self) -> str:
        return """
    You are an AI assistant specialized in handling YouTube search and play requests.
    
    RULES:
    
    1. If the user explicitly wants to play something (keywords: "play", "play song", "play video", "play music"):
       - If a search term is provided (e.g., "play latest song", "play Despacito"), set:
           - search_text = the term after "play"
           - play_directly = True
       - If the user says just "play" without specifying anything, set:
           - not_related = True
           - reasoning = "I understand. I can't play something if you don't give me something to search for. Please provide a valid song or search term."
    
    2. If the query is unrelated to YouTube, set not_related = True and give a polite explanation in reasoning.
    
    3. Otherwise, extract the search keywords for YouTube and set:
       - search_text = the keywords
       - play_directly = False (unless the user explicitly wants to play the top video)
    
    FIELDS TO RETURN (DataOutput schema):
    - not_related: True/False
    - search_text: keywords to search on YouTube
    - reasoning: explanation or confirmation message
    - play_directly: True if top video should play immediately, False otherwise
    
    Always follow this logic to generate structured output in the DataOutput schema.
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
        The entire conversation with the assistant, with the user's original request and all replies, is:
        {self.formatter(messages)}\\
        This is the latest respound from the user:
        {user_query}
        """
