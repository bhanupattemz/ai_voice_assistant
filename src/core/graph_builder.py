from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from src.core.state import AssistantState

# Node Imports
from src.nodes.chatbot_node import ChatbotNode
from src.nodes.calendar_node import CalendarNode
from src.nodes.search_node import SearchNode
from src.nodes.browser_node import BrowserNode

# Edge Imports
from src.edges.redirector_edge import RedirectorEdge

# Tools Imports
from src.tools.calendar_tools import calendar_tools
from src.tools.search_tools import search_tools
from src.tools.browser_tools import browser_tools


class GraphBuilder:
    def __init__(self):
        self.memory = InMemorySaver()

    def build(self):
        graph_builder = StateGraph(AssistantState)
        graph_builder.add_node("chatbot", ChatbotNode().execute)
        graph_builder.add_node("network_search", SearchNode().execute)
        graph_builder.add_node("network_search_tools", ToolNode(tools=search_tools))
        graph_builder.add_node("calendar_node", CalendarNode().execute)
        graph_builder.add_node("calendar_node_tools", ToolNode(tools=calendar_tools))
        graph_builder.add_node("browser_node", BrowserNode().execute)
        graph_builder.add_node("browser_node_tools", ToolNode(tools=browser_tools))

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
            "calendar_node",
            tools_condition,
            {"tools": "calendar_node_tools", "__end__": "chatbot"},
        )
        graph_builder.add_conditional_edges(
            "calendar_node_tools",
            tools_condition,
            {"tools": "calendar_node_tools", "__end__": "chatbot"},
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
        graph_builder.add_edge("chatbot", END)
        return graph_builder.compile(checkpointer=self.memory)
