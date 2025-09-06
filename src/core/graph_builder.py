from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from src.core.state import AssistantState

# Node Imports
from src.nodes.chatbot_node import ChatbotNode
from src.nodes.search_node import SearchNode
from src.nodes.system_node import SystemNode
from src.nodes.softwares_node import SoftwareNode
from src.nodes.calendar.calendar_node import CalendarNode
from src.nodes.calendar.calender_create_node import CreateCalendarNode
from src.nodes.calendar.calendar_update_node import UpdateCalendarNode
from src.nodes.calendar.calendar_delete_node import DeleteCalendarNode
from src.nodes.calendar.calender_final_node import FinalCalendarNode
from src.nodes.keyboard.keyboard_node import KeyboardNode
from src.nodes.keyboard.keyboard_hotkey import KeyboardHotKeyNode
from src.nodes.keyboard.keyboard_presskey import KeyboardPressNode
from src.nodes.keyboard.keyboard_write import KeyboardWriteNode

from src.nodes.youtube_node import YoutubeNode

from src.nodes.chrome.chrome_node import ChromeNode
from src.nodes.chrome.chrome_tab_node import ChromeTabNode
from src.nodes.chrome.chrome_close_node import ChromeCloseNode
from src.nodes.chrome.chrome_func_node import ChromeFuncNode


from src.nodes.filemanage.files_node import FileManagerNode
from src.nodes.filemanage.files_tab_node import FileManagerTabNode
from src.nodes.filemanage.files_close_node import FileManagerCloseNode
from src.nodes.filemanage.files_write_node import FileManagerWriteNode
from src.nodes.filemanage.files_read_node import FileManagerReadNode


# Edge Imports
from src.edges.redirector_edge import RedirectorEdge
from src.edges.calendar_edge import CalendarRedirectorEdge
from src.edges.keyboard_edge import KeyboardRedirectorEdge
from src.edges.chrome_edge import ChromeRedirectorEdge
from src.edges.file_manager_edge import FileManagerRedirectorEdge

# Tools Imports
from src.tools.search_tools import search_tools
from src.tools.system_tools import system_tools
from src.tools.softwares_tool import software_tools
from src.tools.chrome_tab_tools import chrome_tab_tools
from src.tools.chrome_func_tools import chrome_func_tools
from src.tools.files_tab_tools import file_manager_tab_tools
from src.tools.files_write_tools import filemanager_write_tools
from src.tools.files_read_tools import filemanager_read_tools
class GraphBuilder:
    def __init__(self):
        self.memory = InMemorySaver()

    async def build(self):
        """Build the async graph."""

        graph_builder = StateGraph(AssistantState)

        graph_builder.add_node("chatbot", ChatbotNode().execute)
        graph_builder.add_node("network_search", SearchNode().execute)
        graph_builder.add_node("network_search_tools", ToolNode(tools=search_tools))
        graph_builder.add_node("system_node", SystemNode().execute)
        graph_builder.add_node("system_node_tools", ToolNode(tools=system_tools))
        graph_builder.add_node("software_node", SoftwareNode().execute)
        graph_builder.add_node("software_node_tools", ToolNode(tools=software_tools))
        graph_builder.add_node("calendar_node", CalendarNode().execute)
        graph_builder.add_node("calendar_create", CreateCalendarNode().execute)
        graph_builder.add_node("calendar_update", UpdateCalendarNode().execute)
        graph_builder.add_node("calendar_delete", DeleteCalendarNode().execute)
        graph_builder.add_node("calendar_final", FinalCalendarNode().execute)
        graph_builder.add_node("keyboard_node", KeyboardNode().execute)
        graph_builder.add_node("keyboard_hotkey", KeyboardHotKeyNode().execute)
        graph_builder.add_node("keyboard_presskey", KeyboardPressNode().execute)
        graph_builder.add_node("keyboard_write", KeyboardWriteNode().execute)
        graph_builder.add_node("youtube_node", YoutubeNode().execute)
        graph_builder.add_node("chrome_node", ChromeNode().execute)
        graph_builder.add_node("chrome_close_node", ChromeCloseNode().execute)
        graph_builder.add_node("chrome_tab_node", ChromeTabNode().execute)
        graph_builder.add_node("chrome_tab_node_tools", ToolNode(tools=chrome_tab_tools))
        graph_builder.add_node("chrome_func_node", ChromeFuncNode().execute)
        graph_builder.add_node("chrome_func_node_tools", ToolNode(tools=chrome_func_tools))
        
        graph_builder.add_node("filemanager_node", FileManagerNode().execute)
        graph_builder.add_node("filemanager_close_node", FileManagerCloseNode().execute)
        graph_builder.add_node("filemanager_tab_node", FileManagerTabNode().execute)
        graph_builder.add_node("filemanager_tab_node_tools", ToolNode(tools=file_manager_tab_tools))
        graph_builder.add_node("filemanager_write_node", FileManagerWriteNode().execute)
        graph_builder.add_node("filemanager_write_node_tools", ToolNode(tools=filemanager_write_tools))
        graph_builder.add_node("filemanager_read_node", FileManagerReadNode().execute)
        graph_builder.add_node("filemanager_read_node_tools", ToolNode(tools=filemanager_read_tools))
        

        graph_builder.add_conditional_edges(START, RedirectorEdge().execute)

        graph_builder.add_conditional_edges(
            "network_search",
            tools_condition,
            {"tools": "network_search_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "network_search_tools",
            tools_condition,
            {"tools": "network_search_tools", "__end__": "chatbot"},
        )
        
        graph_builder.add_conditional_edges(
            "system_node",
            tools_condition,
            {"tools": "system_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "system_node_tools",
            tools_condition,
            {"tools": "system_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "software_node",
            tools_condition,
            {"tools": "software_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "software_node_tools",
            tools_condition,
            {"tools": "software_node_tools", "__end__": "chatbot"},
        )
        
        graph_builder.add_conditional_edges(
            "chrome_tab_node",
            tools_condition,
            {"tools": "chrome_tab_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "chrome_tab_node_tools",
            tools_condition,
            {"tools": "chrome_tab_node_tools", "__end__": "chatbot"},
        )
        
        graph_builder.add_conditional_edges(
            "chrome_func_node",
            tools_condition,
            {"tools": "chrome_func_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "chrome_func_node_tools",
            tools_condition,
            {"tools": "chrome_func_node_tools", "__end__": "chatbot"},
        )
        
        
        graph_builder.add_conditional_edges(
            "filemanager_tab_node",
            tools_condition,
            {"tools": "filemanager_tab_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "filemanager_tab_node_tools",
            tools_condition,
            {"tools": "filemanager_tab_node_tools", "__end__": "chatbot"},
        )
        
        graph_builder.add_conditional_edges(
            "filemanager_write_node",
            tools_condition,
            {"tools": "filemanager_write_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "filemanager_write_node_tools",
            tools_condition,
            {"tools": "filemanager_write_node_tools", "__end__": "chatbot"},
        )
        
        graph_builder.add_conditional_edges(
            "filemanager_read_node",
            tools_condition,
            {"tools": "filemanager_read_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "filemanager_read_node_tools",
            tools_condition,
            {"tools": "filemanager_read_node_tools", "__end__": "chatbot"},
        )

        graph_builder.add_conditional_edges(
            "calendar_node", CalendarRedirectorEdge().execute
        )
        graph_builder.add_conditional_edges(
            "keyboard_node", KeyboardRedirectorEdge().execute
        )
        graph_builder.add_conditional_edges(
            "chrome_node", ChromeRedirectorEdge().execute
        )
        graph_builder.add_conditional_edges(
            "filemanager_node", FileManagerRedirectorEdge().execute
        )

        graph_builder.add_edge("calendar_create", "calendar_final")
        graph_builder.add_edge("calendar_update", "calendar_final")
        graph_builder.add_edge("calendar_delete", "calendar_final")
        graph_builder.add_edge("calendar_final", "chatbot")

        graph_builder.add_edge("keyboard_hotkey", "chatbot")
        graph_builder.add_edge("keyboard_presskey", "chatbot")
        graph_builder.add_edge("keyboard_write", "chatbot")
        graph_builder.add_edge("youtube_node", "chatbot")
        graph_builder.add_edge("chrome_tab_node","chatbot")
        graph_builder.add_edge("chrome_close_node","chatbot")
        graph_builder.add_edge("chrome_func_node","chatbot")
        graph_builder.add_edge("filemanager_tab_node","chatbot")
        graph_builder.add_edge("filemanager_close_node","chatbot")
        graph_builder.add_edge("filemanager_write_node","chatbot")
        graph_builder.add_edge("filemanager_read_node","chatbot")
        graph_builder.add_edge("chatbot", END)
        return graph_builder.compile(checkpointer=self.memory)
