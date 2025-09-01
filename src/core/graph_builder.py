from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from src.core.state import AssistantState

# Node Imports
from src.nodes.chatbot_node import ChatbotNode
from src.nodes.search_node import SearchNode
from src.nodes.browser_node import BrowserNode
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

# Edge Imports
from src.edges.redirector_edge import RedirectorEdge
from src.edges.calendar_edge import CalendarRedirectorEdge
from src.edges.keyboard_edge import KeyboardRedirectorEdge

# Tools Imports
from src.tools.search_tools import search_tools
from src.tools.browser_tools import browser_tools
from src.tools.system_tools import system_tools
from src.tools.softwares_tool import software_tools


class GraphBuilder:
    def __init__(self):
        self.memory = InMemorySaver()

    async def build(self):
        """Build the async graph."""

        graph_builder = StateGraph(AssistantState)

        graph_builder.add_node("chatbot", ChatbotNode().execute)
        graph_builder.add_node("network_search", SearchNode().execute)
        graph_builder.add_node("network_search_tools", ToolNode(tools=search_tools))
        graph_builder.add_node("browser_node", BrowserNode().execute)
        graph_builder.add_node("browser_node_tools", ToolNode(tools=browser_tools))
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
            "browser_node",
            tools_condition,
            {"tools": "browser_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "browser_node_tools",
            tools_condition,
            {"tools": "browser_node_tools", "__end__": "chatbot"},
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
            "calendar_node", CalendarRedirectorEdge().execute
        )
        graph_builder.add_conditional_edges(
            "keyboard_node", KeyboardRedirectorEdge().execute
        )

        graph_builder.add_edge("calendar_create", "calendar_final")
        graph_builder.add_edge("calendar_update", "calendar_final")
        graph_builder.add_edge("calendar_delete", "calendar_final")
        graph_builder.add_edge("calendar_final", "chatbot")

        graph_builder.add_edge("keyboard_hotkey", "chatbot")
        graph_builder.add_edge("keyboard_presskey", "chatbot")
        graph_builder.add_edge("keyboard_write", "chatbot")
        graph_builder.add_edge("chatbot", END)
        return graph_builder.compile(checkpointer=self.memory)

    